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


from .database import get_db, engine
from . import models

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
            options.add_argument("--disable-dev-sh-usage")
            options.add_argument('--window-size=1420,1080')
            options.add_argument("--disable-software-rasterizer")
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
            # print({"message2": soup})
            # Find all the job vacancies on the page
            vacancies = soup.find_all('li', class_="vacancy-item")
            print(f"vacancies size: {len(vacancies)}")
            for vacancy in vacancies:
                vacancy_name = vacancy.find('h4', class_="mb-2").text
                vacancy_link = vacancy.a['href']
                vacancy_start_date = vacancy.find('div', class_="italic text-gray-400").text
                is_vacancy_closed = vacancy.find('p', string="Регистрация временно приостановлена")

                # if vacancy is open
                if  is_vacancy_closed:
                    new_vacancy = models.Vacancy(email=e, name=vacancy_name, link=vacancy_link, start=vacancy_start_date) 
                    db.add(new_vacancy)
                    db.commit()
                    db.refresh(new_vacancy)

                    driver.get("https://agropraktika.eu/")  
                    main_html = driver.page_source
                    soup_second = BeautifulSoup(main_html, 'lxml')
                    print({"message": soup_second})

                    WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.NAME, "email"))) 
                    # Find the login and password input fields and fill them in
                    email_input = driver.find_element(By.NAME, "email")
                    email_input.send_keys(e)

                    password_input = driver.find_element(By.NAME, "password")
                    password_input.send_keys(p)

                    login_btn = driver.find_element(By.ID, "ugo1")
                    login_btn.click()

                    # Wait for the page to load after login and get the current URL
                    
                    WebDriverWait(driver, 30).until(EC.visibility_of_all_elements_located((By.ID, "photo"))) 

                    # Check if the current URL redirected to url
                    if driver.current_url == "https://agropraktika.eu/user/profile":
                        print("Login successful!")

                        # Redirect to new vacancy's link
                        driver.get(new_vacancy.link)

                        # # wait for the page load
                        # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'Подать заявку')]")))

                        # # tap to apply button
                        # apply_button = driver.find_element(By.XPATH, "//button[contains(text(),'Подать заявку')]")
                        # apply_button.click()
                        break
                    else:
                        print("Couldn't login") 
            driver.quit()        
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
      
    
    







        
    
    