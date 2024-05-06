from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
import re
import time

def init_driver(headless=True):
    """Initialize the Selenium WebDriver."""
    options = Options()
    options.headless = headless
    options.add_argument("--enable-javascript")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
    options.add_argument("--enable-javascript")
    options.add_argument("--ignore-certificate-errors")
    return webdriver.Chrome(options=options)

def find_terms_link(element):
    """Function to locate a terms of service link using various criteria."""
    text = element.get_attribute('innerText')
    href = element.get_attribute('href')
    terms_patterns = [
        'terms of service', 'terms and conditions', 'terms & conditions',
        'terms', 'terms of use',
    ]
    pattern = re.compile('|'.join(terms_patterns), re.IGNORECASE)
    return pattern.search(text) or pattern.search(href)

def is_terms_of_service_page(content):
    """Check if the current page is likely the Terms of Service page."""
    soup = BeautifulSoup(content, 'html.parser')
    time.sleep(5)
    headers = ['h1', 'h2', 'h3']
    for header in headers:
         if soup.find(header, string=lambda text: text and "terms of service" in text):
             
            return True
            time.sleep(5)
    time.sleep(5)
    return False



def navigate_to_tos(driver, url):
    driver.get(url)
    initial_page_source = driver.page_source
    
    cookies = driver.get_cookies()
    for cookie in cookies:
        driver.add_cookie(cookie)
        
    if is_terms_of_service_page(initial_page_source):
        print("Already on the Terms of Service page.")
        return initial_page_source
    else:
        try:
            footer_links = driver.find_elements(By.CSS_SELECTOR, 'footer a')
            terms_link = next((link for link in footer_links if find_terms_link(link)), None)
            
            if terms_link:
                terms_link.click()
            else:
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                terms_link = next((link for link in all_links if find_terms_link(link)), None)
                if terms_link:
                    terms_link.click()
            
           
            WebDriverWait(driver, 10)
            return driver.page_source

        except TimeoutException:
            print("Timed out waiting for terms of service page to load.")
        except StopIteration:
            print("No Terms of Service link found.")
        except Exception as e:
            print(f"Error navigating to Terms of Service page: {e}")
        return None

def get_tos_content(url):
    """Public function to get Terms of Service content."""
    driver = init_driver(headless=True)
    try:
        page_source = navigate_to_tos(driver, url)
        if page_source:
            return get_text_from_tos_page(page_source)
        else:
            print("Failed to retrieve the Terms of Service page.")
            return None
    finally:
        driver.quit()

def get_text_from_tos_page(content):
    """Extract all text from the Terms of Service page after the 'Terms of Service' header."""
    soup = BeautifulSoup(content, 'html.parser')

   
    pattern = re.compile(r"terms of service", re.IGNORECASE)
    tos_header = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and pattern.search(tag.get_text()))

    if tos_header:
        content = []
        element = tos_header.find_next()
        while element:
            if element.name in ['h1']:
                break 
            if element.get_text(strip=True):
                content.append(element.get_text(strip=True))
            element = element.find_next()
        return '\n'.join(content)
    else:
        return "Terms of Service section not found."

if __name__ == '__main__':
    url = 'https://www.tripadvisor.com/'
    tos_text = get_tos_content(url)
    if tos_text:
        print(tos_text)
    else:
        print("No ToS content found.")
