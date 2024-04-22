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
    options = Options()
    options.add_argument("--ignore-certificate-errors")
    # Ensure the executable_path is set to the location of your WebDriver if not in PATH
    return webdriver.Chrome(options=options)

def find_terms_link(element):
    """Function to locate a terms of service link using various criteria."""
    text = element.get_attribute('innerText')
    href = element.get_attribute('href')
    # Regular expression to match different common terms of service texts
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
    # Define the headers you expect 'Terms of Service' might appear in
    headers = ['h1', 'h2', 'h3']
    # Look for the text in the headers
    for header in headers:
         if soup.find(header, string=lambda text: text and "terms of service" in text):
             
            return True
            time.sleep(5)
    time.sleep(5)
    return False



def navigate_to_tos(driver, url):
    driver.get(url)
    initial_page_source = driver.page_source
    
    if is_terms_of_service_page(initial_page_source):
        print("Already on the Terms of Service page.")
        return initial_page_source
    else:
        try:
            # Attempt to find the Terms of Service link within common locations first
            footer_links = driver.find_elements(By.CSS_SELECTOR, 'footer a')
            terms_link = next((link for link in footer_links if find_terms_link(link)), None)
            
            if terms_link:
                terms_link.click()
            else:
                # Fall back to searching the whole page if not found in the footer
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                terms_link = next((link for link in all_links if find_terms_link(link)), None)
                if terms_link:
                    terms_link.click()
            
            # Wait for the page to load after clicking
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
    driver = init_driver(headless=True)  # Set headless to False if you want to see the browser
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
    """Extract all text from the Terms of Service page."""
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text()

if __name__ == '__main__':
    # Test the function with a URL
    url = 'https://www.indeed.com'
    tos_text = get_tos_content(url)
    if tos_text:
        print(tos_text)
    else:
        print("No ToS content found.")
