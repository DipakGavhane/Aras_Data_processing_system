from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import time


class Extraction:
    def __init__(self):
        self.soup = None
        self.driver = None
        self.chrome_option = webdriver.ChromeOptions()
        self.chrome_option.add_experimental_option("detach", True)
        self.chrome_option.add_argument("--headless")  # Runs Chrome in background

    def set_driver(self):
        self.driver = webdriver.Chrome(options=self.chrome_option)
        self.driver.get(url="https://sgbau.ucanapply.com/result-details")

    def select_options(self):
        # time.sleep(2)
        dropdown_element = self.driver.find_element(By.XPATH, value='//*[@id="session"]')
        select_object = Select(dropdown_element)
        select_object.select_by_visible_text("Summer 2024")

        dropdown_element = self.driver.find_element(By.XPATH, value='//*[@id="coursetype"]')
        select_object = Select(dropdown_element)
        select_object.select_by_visible_text("UG")

        time.sleep(1)
        course_btn = self.driver.find_element(By.XPATH, value='//*[@id="result-search-panal"]/div[1]/div[3]/div/div/button')
        course_btn.click()

        course_search = self.driver.find_element(By.XPATH, value='//*[@id="result-search-panal"]/div[1]/div[3]/div/'
                                                            'div/div/div[1]/input')
        course_search.send_keys("bca")
        course_search.send_keys(Keys.ENTER)

        time.sleep(1)
        dropdown_element = self.driver.find_element(By.XPATH, value='//*[@id="resulttype"]')
        select_object = Select(dropdown_element)
        select_object.select_by_visible_text("Regular")

        # time.sleep(1)
        rollno_field = self.driver.find_element(By.XPATH, value='//*[@id="username"]')
        rollno_field.send_keys(f'22AK111455')

        # time.sleep(1)
        dropdown_element = self.driver.find_element(By.XPATH, value='//*[@id="semester"]')
        select_object = Select(dropdown_element)
        select_object.select_by_visible_text("Fourth Semester ( Sem - 4)")

        final_btn = self.driver.find_element(By.XPATH, value='//*[@id="result-search-panal"]/div[2]/div[1]/button')
        final_btn.click()
        # self.get_html_code()

    def get_credentials(self):
        """This method will return authentication key's"""
        try:
            # In Cookies, We get two keys : Session & XSRF
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            # In Html code, We get a _token as hidden field
            token_element = self.driver.find_element("xpath",
                                                     '//*[@id="result-search-panal"]/input[1]')
            token_value = token_element.get_attribute("value")

            cookie_dict['_token'] = token_value
            return cookie_dict

        except Exception as e:
            print("Error fetching cookies:", e)

    def get_html_code(self):
        # Get page source from Selenium WebDriver
        result_html = self.driver.page_source
        # self.driver.quit()

        # Pass the result HTML to BeautifulSoup
        self.soup = BeautifulSoup(result_html, 'html.parser')
        data = self.soup.find("div", id="resultDetails_view")
        # print(self.soup.prettify())  # Optionally print to verify HTML content is correct
        print(data.prettify())

    def close_webdriver(self):
        self.driver.quit()






