import requests
from bs4 import BeautifulSoup

def scrape_tos(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        tos_text = '\n'.join([p.get_text() for p in paragraphs])
        return tos_text
    else:
        return "Failed to retrieve the webpage"
