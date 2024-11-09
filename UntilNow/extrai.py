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

# URL de filtro e domínio base
base_url = "https://www.infojobs.com.br/company/candidate/list2.aspx?ps=20&pn={page_num}&ilo=64&kw=Padeiro&icst=2&iv=1"
base_domain = "https://www.infojobs.com.br"

# Limite de links a extrair
link_limit = 10

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
        json.dump(links, file, indent=4, ensure_ascii=False)

try:
    # Acessa a página de login
    driver.get("https://login.infojobs.com.br/Account/Login")
    time.sleep(2)

    # Fecha o pop-up de cookies, se presente
    try:
        cookie_button = driver.find_element(By.ID, "didomi-notice-agree-button")
        cookie_button.click()
        print("Pop-up de cookies fechado.")
    except NoSuchElementException:
        print("Pop-up de cookies não encontrado.")

    # Tenta carregar cookies, se existirem
    try:
        load_cookies(driver, cookies_path)
        driver.refresh()
        print("Cookies carregados e sessão restaurada.")
        driver.get(base_url.format(page_num=1))  # Redireciona para a URL original de filtro após carregar os cookies
    except FileNotFoundError:
        print("Cookies não encontrados, realizando login manual.")
        email_field = wait.until(EC.presence_of_element_located((By.ID, "Email")))
        email_field.send_keys("litoralRepresentacoess@gmail.com")
        continuar_button = driver.find_element(By.CLASS_NAME, "js_loginButton")
        continuar_button.click()

        password_field = wait.until(EC.presence_of_element_located((By.ID, "Password")))
        password_field.send_keys("786!iodfpsjafpoA")
        acessar_button = driver.find_element(By.CLASS_NAME, "js_loginButton")
        acessar_button.click()

        save_cookies(driver, cookies_path)
        print("Login bem-sucedido e cookies salvos.")

        # Redireciona para a URL de filtro após login
        driver.get(base_url.format(page_num=1))

    candidate_links = []
    page_num = 1

    while len(candidate_links) < link_limit:
        # Acessa a URL da página atual
        url = base_url.format(page_num=page_num)
        driver.get(url)
        time.sleep(2)

        # Extrair links de cada candidato
        candidates = driver.find_elements(By.CLASS_NAME, "js_candidate")

        if not candidates:
            print("Nenhum candidato encontrado na página, encerrando a navegação.")
            break

        for candidate in candidates:
            if len(candidate_links) >= link_limit:
                break

            try:
                link_element = candidate.find_element(By.CSS_SELECTOR, "a.js_ViewCV_btn")
                link = link_element.get_attribute("href")
                full_link = base_domain + link if link.startswith("/") else link
                candidate_links.append({"link": full_link})
                print(f"Link extraído: {full_link}")
            except NoSuchElementException:
                print("Elemento de link de detalhes não encontrado para um candidato.")

        page_num += 1

    # Salva os links no arquivo JSON
    save_links_to_json(candidate_links, links_json_path)
    print(f"Links salvos em {links_json_path}")

except TimeoutException:
    print("Timeout ao tentar encontrar um elemento.")
finally:
    print("Finalizamos o processo....")
    driver.quit()
