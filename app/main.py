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


from .database import get_db, engine
from . import models


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
    # check if bot already applied for a job for this email
    is_full = db.query(models.Vacancy).filter(models.Vacancy.email == e).all()

    if not is_full :

        # URL of the website to scrape
        url = "https://agropraktika.eu/vacancies?l=united-kingdom"

        # Make a GET request to the website and parse the HTML using Beautiful Soup
        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'lxml')

        # Find all the job vacancies on the page
        vacancies = soup.find_all('li', class_="vacancy-item")

        for vacancy in vacancies:

            vacancy_name = vacancy.find('h4', class_="mb-2").text
            vacancy_link = vacancy.a['href']
            vacancy_start_date = vacancy.find('div', class_="italic text-gray-400").text
            is_vacancy_closed = vacancy.find('p', string="Регистрация временно приостановлен")

            # if vacancy is open
            if not is_vacancy_closed:
                
                new_vacancy = models.Vacancy(email=e, name=vacancy_name, link=vacancy_link, start=vacancy_start_date) 
                db.add(new_vacancy)
                db.commit()
                db.refresh(new_vacancy)

                # chromedriver path
                chromedriver_path = "chromedriver.exe"

                # Path of chromedriver
                service = Service(executable_path=chromedriver_path)

                # Create a new instance of the Chrome driver
                driver = webdriver.Chrome(service=service)
                driver.get("https://agropraktika.eu/")  

                # Find the login and password input fields and fill them in
                email_input = driver.find_element(By.NAME, "email")
                email_input.send_keys(e)

                password_input = driver.find_element(By.NAME, "password")
                password_input.send_keys(p)

                login_btn = driver.find_element(By.ID, "ugo1")
                login_btn.click()

                # Wait for the page to load after login and get the current URL
                wait = WebDriverWait(driver, 10)
                wait.until(EC.visibility_of_all_elements_located((By.ID, "photo"))) 

                # Check if the current URL redirected to url
                if driver.current_url == "https://agropraktika.eu/user/profile":
                    print("Login successful!!!")

                    # Redirect to new vacancy's link
                    driver.get(new_vacancy.link)

                    # # wait for the page load
                    # wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'Подать заявку')]")))

                    # # tap to apply button
                    # apply_button = driver.find_element(By.XPATH, "//button[contains(text(),'Подать заявку')]")
                    # apply_button.click()
                    break
                else:
                    print("Couldn't login") 
                
                driver.quit()
    else:
        print("already applied")



        
    
    