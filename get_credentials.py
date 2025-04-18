from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


class Extraction:
    def __init__(self):
        self.soup = None
        self.driver = None
        self.chrome_option = webdriver.ChromeOptions()
        self.chrome_option.add_experimental_option("detach", True)
        self.chrome_option.binary_location = "/usr/bin/chromium"
        self.chrome_option.add_argument("--headless")  # Runs Chrome in background
        self.chrome_option.add_argument("--no-sandbox")
        self.chrome_option.add_argument("--disable-dev-shm-usage")

    def set_driver(self):
        # Explicitly specify the ChromeDriver path
        service = Service("/usr/local/bin/chromedriver")  # Correct way to specify path
        self.driver = webdriver.Chrome(service=service, options=self.chrome_option)
        # self.driver = webdriver.Chrome(options=self.chrome_option)
        self.driver.get(url="https://sgbau.ucanapply.com/result-details")

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






