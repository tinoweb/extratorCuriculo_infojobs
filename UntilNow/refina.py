import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, InvalidCookieDomainException

# Configuração do WebDriver
options = Options()
options.add_argument("--width=1200")
options.add_argument("--height=800")
options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36")
driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 30)

# Caminhos para os arquivos de cookies e links JSON
cookies_path = "cookies.json"
links_json_path = "candidatos_links.json"
output_json_path = "candidatos_dados.json"

# Limite de links a serem visitados
visit_limit = 5  # Defina o limite desejado

# Função para carregar cookies
def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            cookie["domain"] = ".infojobs.com.br"  # Força o domínio correto para os cookies
            try:
                driver.add_cookie(cookie)
            except InvalidCookieDomainException:
                print("Tentativa de carregar cookie para o domínio errado. Ignorando.")

# Função para salvar dados extraídos em JSON
def save_data_to_json(data, path):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Função para carregar links dos candidatos
def load_links(path):
    with open(path, 'r', encoding='utf-8') as file:
        links_data = json.load(file)
        # Se o arquivo for um mapa, converte para lista de URLs
        links = [entry["link"] for entry in links_data] # Assumindo que cada valor contém uma chave 'link'
        return links

# Carrega os links dos candidatos
candidate_links = load_links(links_json_path)
extracted_data = []

# Acessa o domínio principal para garantir o carregamento correto dos cookies
driver.get("https://www.infojobs.com.br")
time.sleep(2)

# Carrega os cookies para manter a sessão ativa
try:
    load_cookies(driver, cookies_path)
    driver.refresh()
    print("Cookies carregados e sessão restaurada.")
except FileNotFoundError:
    print("Arquivo de cookies não encontrado. Realize o login manualmente primeiro para gerar os cookies.")
    driver.quit()
    exit()

# Verifica se o login está ativo acessando o painel do usuário ou um link restrito
driver.get("https://www.infojobs.com.br/candidate/")
time.sleep(3)  # Espera extra para garantir que a sessão esteja ativa

# Contador de links visitados
visited_count = 0

# Itera sobre cada link no JSON
for link_data in candidate_links:
    if visited_count >= visit_limit:
        print("Limite de visitas atingido.")
        break

    driver.get(link_data)
    time.sleep(3)  # Aguarda carregar a página do candidato

    try:
        # # Clica no botão para visualizar os dados de contato
        # Verifica se o botão "Visualizar dados de contato" está visível (sem a classe 'hidden') e clica
        try:
            contact_info_button = driver.find_element(By.CSS_SELECTOR, "div.js_divBtnShowContactInfo")
            if "hidden" not in contact_info_button.get_attribute("class"):
                contact_info_button.click()
                print("Botão 'Visualizar dados de contato' clicado.")
                time.sleep(2)  # Aguarda a sessão de contato expandir
            else:
                print("Botão 'Visualizar dados de contato' já está visível ou não requer interação.")
        except NoSuchElementException:
            print("Botão 'Visualizar dados de contato' não encontrado.")

        # Extrai as informações de contato
        try:
            parent_element = driver.find_element(By.CSS_SELECTOR, "div.firstInfo.mb-0")
            name = parent_element.find_element(By.TAG_NAME, "h1").text
            
            try:
                phone_element = driver.find_element(By.XPATH, "//a[contains(@href, 'https://wa.me/')]")
                phone = phone_element.text
            except NoSuchElementException:
                phone = ""  # Define como vazio se o número de telefone não for encontrado

            age = driver.find_element(By.CSS_SELECTOR, "h1 span").text

            last_update = driver.find_element(By.CLASS_NAME, "last").text
            
            # email_element = driver.find_element(By.CSS_SELECTOR, "div.email")
            # email = email_element.find_element(By.CLASS_NAME, "js_contactEmail").text
            try:
                email_element = driver.find_element(By.CSS_SELECTOR, "div.email")
                email = email_element.find_element(By.CLASS_NAME, "js_contactEmail").text
            except NoSuchElementException:
                # Se não for encontrado, tenta extrair o email usando o seletor alternativo
                try:
                    email_element = driver.find_element(By.CSS_SELECTOR, "div.email.m-0")
                    email = email_element.find_element(By.CLASS_NAME, "js_lnkMail").text
                except NoSuchElementException:
                    email = ""  # Define como vazio se o email não for encontrado

            try:
                # Primeira tentativa de extração da localização
                location_element = driver.find_element(By.CSS_SELECTOR, "div.location")
                location = location_element.find_element(By.CLASS_NAME, "js_contactLocation").text
            except NoSuchElementException:
                # Se a primeira tentativa falhar, usa o seletor alternativo
                try:
                    location_element = driver.find_element(By.CSS_SELECTOR, "div.location.m-0")
                    location = location_element.text  # Extrai o texto diretamente do elemento alternativo
                except NoSuchElementException:
                    location = ""  # Define como vazio se a localização não for encontrada em nenhuma das tentativas


            # Extrai o último emprego
            last_job = driver.find_element(By.ID, "ctl00_phMasterPage_cCV_cCandidateResume_liLastJob").text

            # Extrai o último estudo
            last_study = driver.find_element(By.ID, "ctl00_phMasterPage_cCV_cCandidateResume_liLastStudie").text

            # Armazena os dados extraídos
            candidate_data = {
                "name": name,
                "age": age,
                "last_update": last_update,
                "phone": phone,
                "email": email,
                "location": location,
                "last_job": last_job,
                "last_study": last_study,
            }
            extracted_data.append(candidate_data)
            print(f"Dados extraídos para {name}")

            visited_count += 1

        except NoSuchElementException as e:
            print(f"Elemento não encontrado: {e}")
            continue

    except TimeoutException:
        print("Timeout ao carregar a página do candidato.")
        continue


# Salva os dados extraídos em um arquivo JSON
save_data_to_json(extracted_data, output_json_path)
print(f"Dados salvos em {output_json_path}")

# Fecha o navegador
driver.quit()
