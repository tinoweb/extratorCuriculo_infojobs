import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidCookieDomainException

# Configuração do WebDriver
options = Options()
options.add_argument("--width=1200")
options.add_argument("--height=800")
options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36")
driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 30)

# Caminho para o arquivo de cookies e JSON
cookies_path = "cookies.json"
links_json_path = "candidatos_links.json"

# Função para salvar cookies
def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)

# Função para carregar cookies
def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except InvalidCookieDomainException:
                print("Tentativa de carregar cookie para o domínio errado. Ignorando.")

# Função para salvar links em JSON
def save_links_to_json(links, path):
    with open(path, 'w') as file:
        json.dump(links, file, indent=4)

try:
    # Acessa a página de login para garantir o domínio correto para cookies
    driver.get("https://login.infojobs.com.br/Account/Login")
    time.sleep(2)  # Aguarda carregar

    # Fecha o pop-up de cookies se estiver presente
    try:
        cookie_button = driver.find_element(By.ID, "didomi-notice-agree-button")  # Ajuste o seletor se necessário
        cookie_button.click()
        print("Pop-up de cookies fechado.")
    except NoSuchElementException:
        print("Pop-up de cookies não encontrado, prosseguindo com o login.")

    # Carrega cookies, se existir, no domínio correto
    try:
        load_cookies(driver, cookies_path)
        driver.refresh()
        print("Cookies carregados e sessão restaurada.")
    except FileNotFoundError:
        # Processo de login se cookies não existirem
        email_field = wait.until(EC.presence_of_element_located((By.ID, "Email")))
        email_field.send_keys("litoralRepresentacoess@gmail.com")
        continuar_button = driver.find_element(By.CLASS_NAME, "js_loginButton")
        continuar_button.click()

        password_field = wait.until(EC.presence_of_element_located((By.ID, "Password")))
        password_field.send_keys("786!iodfpsjafpoA")
        acessar_button = driver.find_element(By.CLASS_NAME, "js_loginButton")
        acessar_button.click()

        wait.until(EC.url_contains("Dashboard"))  # Confirma login
        save_cookies(driver, cookies_path)
        print("Cookies salvos após login bem-sucedido.")

    # Acessa a página com filtros
    driver.get("https://www.infojobs.com.br/company/candidate/list2.aspx?ps=20&pn=1&ilo=64&kw=Padeiro&icst=2&iv=1")
    time.sleep(2)  # Espera a página carregar

    # Extrair links de cada candidato
    candidate_links = []
    candidates = driver.find_elements(By.CLASS_NAME, "js_candidate")
    
    for candidate in candidates:
        try:
            link_element = candidate.find_element(By.CSS_SELECTOR, "a.js_Print_btn")
            link = link_element.get_attribute("href")
            candidate_links.append({"link": link})
            print(f"Link extraído: {link}")
        except NoSuchElementException:
            print("Elemento de link não encontrado para um candidato.")

    # Salva os links no arquivo JSON
    save_links_to_json(candidate_links, links_json_path)
    print(f"Links salvos em {links_json_path}")

except TimeoutException:
    print("Timeout ao tentar encontrar um elemento.")
finally:
    driver.quit()
