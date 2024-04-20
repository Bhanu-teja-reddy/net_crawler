import requests
from bs4 import BeautifulSoup

# def scrape_tos(url):
#     response = requests.get(url)
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, 'html.parser')
#         paragraphs = soup.find_all('p')
#         tos_text = '\n'.join([p.get_text() for p in paragraphs])
#         return tos_text
#     else:
#         return "Failed to retrieve the webpage"
def scrape_tos(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    tos_content = '\n'.join([p.get_text() for p in paragraphs])
    return tos_content.text if tos_content else "No Terms of service found."