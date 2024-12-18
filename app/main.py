from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
import os
import requests
import http.client, urllib

from .database import get_db, engine
from . import models
from .config import settings

import time

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def url_to_be_any_of(*urls):
    def _predicate(driver):
        current_url = driver.current_url
        return current_url in urls
    return _predicate
     
@app.get("/apply")
def apply(e: str, p: str, db: Session = Depends(get_db)):
    driver = None
    try:
        # check if bot already applied for a job for this email
        is_full = db.query(models.Vacancy).filter(models.Vacancy.email == e).all()
    
        if not is_full :
            
            # This part for bypass bot-blocker no site
            options = Options()
            options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

            options.add_argument(f"user-agent={user_agent}")
            options.add_argument("--headless")  # Запуск в фоновом режиме
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--window-size=1420,1080')
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--incognito")
            # options.add_argument("--disable-software-rasterizer")
            # 
            
            service = Service(executable_path=os.environ.get('CHROMEDRIVER_PATH'))
 
            driver = webdriver.Chrome(service=service, options=options)

            # URL of the website to scrape
            url = "https://agropraktika.eu/vacancies?l=united-kingdom"
            driver.get(url)
            
            WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "vacancy-item"))
            )

            html_text = driver.page_source
            soup = BeautifulSoup(html_text, 'lxml')
            
            # Find all the job vacancies on the page
            vacancies = soup.find_all('li', class_="vacancy-item")
            
            for vacancy in vacancies:
                vacancy_name = vacancy.find('h4', class_="mb-2").text
                vacancy_link = vacancy.a['href']
                vacancy_start_date = vacancy.find('div', class_="italic text-gray-400").text
                is_vacancy_closed = vacancy.find('p', string="Регистрация временно приостановлена")

                # if vacancy is open
                if not is_vacancy_closed:
                    new_vacancy = models.Vacancy(email=e, name=vacancy_name, link=vacancy_link, start=vacancy_start_date) 
                    
                    driver.get("https://agropraktika.eu/")  

                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "email"))) 
                    # Find the login and password input fields and fill them in
                    email_input = driver.find_element(By.NAME, "email")
                    email_input.send_keys(e)
                    
                    password_input = driver.find_element(By.NAME, "password")
                    password_input.send_keys(p)
                    
                    login_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Войти')]")))
                    login_btn.click()
                    
                    time.sleep(5)
                    driver.get("https://agropraktika.eu/user/profile")
                    

                    # Wait for the page to load after login and get the current URL
                    
                    WebDriverWait(driver, 20).until(url_to_be_any_of("https://agropraktika.eu/user/profile", "https://agropraktika.eu/user/applications"))
                    if driver.current_url in ["https://agropraktika.eu/user/profile", "https://agropraktika.eu/user/applications"]:
                        print("Login successful!")

                        # Redirect to new vacancy's link
                        driver.get(new_vacancy.link)

                        # tap to apply button
                        apply_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Подать заявку')]")))
                        apply_button.click()

                        db.add(new_vacancy)
                        db.commit()
                        db.refresh(new_vacancy)

                         #  sending notification using pushover
                        payload = {
                            "token": settings.api_token,  # Ваш API токен
                            "user": settings.user_key,  # Ваш User ключ
                            "message": "Ваша заявка была подана. Пожалуйста, проверьте сайт Агропрактики. С уважением, Ваш спаситель, Неж."
                        }
                        requests.post("https://api.pushover.net:443/1/messages.json", data=payload)

                        return {"message": f"job successfully applied for user {e}"}
                    else:
                         #  sending notification using pushover
                        payload = {
                            "token": settings.api_token,  # Ваш API токен
                            "user": settings.user_key,  # Ваш User ключ
                            "message": f"Есть открытая вакансия. Но возникли проблемы при регистрации аккаунта {new_vacancy.link}" 
                        }
                        requests.post("https://api.pushover.net:443/1/messages.json", data=payload)

                        print("Couldn't login") 
                        return {"message": f"ERORR WHILE LOGIN IN {e} {driver.current_url}"}        
        else:
            print("already applied!")
    finally:
        if driver:
            driver.quit()
        
       
            
    
    

@app.get("/test")
def apply(e: str, p: str, db: Session = Depends(get_db)):
   

    options = Options()
    options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")  # Запуск в фоновом режиме
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-sh-usage")
    options.add_argument('--window-size=1420,1080')
    

    service = Service(executable_path=os.environ.get('CHROMEDRIVER_PATH'))

    driver = webdriver.Chrome(service=service, options=options)

    # URL of the website to scrape
    url = "https://agropraktika.eu/vacancies?l=united-kingdom"

    driver.get(url)
    time.sleep(1)

    html_text = driver.page_source
    soup = BeautifulSoup(html_text, 'lxml')
    print("im passed through here x1")

    # Find all the job vacancies on the page
    vacancies = soup.find_all('li', class_="vacancy-item")
    print(vacancies)
    print({"message2": soup})

    driver.quit()


@app.get('/pushover')
def pushover():
    try:    
        payload = {
            "token": settings.api_token,  # Ваш API токен
            "user": settings.user_key,  # Ваш User ключ
            "message": "Ваша заявка была подана. Пожалуйста, проверьте сайт Агропрактики. С уважением, Ваш спаситель, Неж."
        }
        
        response = requests.post("https://api.pushover.net:443/1/messages.json", data=payload)

        if response.status_code == 200:
            return {"message": "Your notification sent"}
        else:
            return {"message": f"Error occurred: {response.status_code}, {response.text}"}

    except:
        return {"message": "Error accured while sending notificaiton"}

    
    







        
    
    