import requests
from bs4 import BeautifulSoup
import re
from urllib.robotparser import RobotFileParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def can_fetch(url):
    rp = RobotFileParser()
    rp.set_url(url + '/robots.txt')
    rp.read()
    user_agent = '*'  # or specify your bot's user agent
    return rp.can_fetch(user_agent, url)

def fetch_page(url):
    if not can_fetch(url):
        print(f"Fetching disallowed by robots.txt: {url}")
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None

def scrape_and_process_tos(url):
    if not can_fetch(url):
        return None
    
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    content = driver.page_source
    driver.quit()

    soup = BeautifulSoup(content, 'html.parser')
    text = ' '.join(soup.stripped_strings)
    # Naive method to locate Terms of Service
    # For better results, use an NLP model or more complex heuristics
    tos_start = text.find('Terms of Service')
    tos_end = text.find('Privacy Policy', tos_start)
    if tos_start != -1 and tos_end != -1:
        return text[tos_start:tos_end]
    return None
