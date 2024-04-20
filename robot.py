import requests
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

def is_allowed_to_scrape(url, user_agent='MyWebScraper'):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    robots_txt_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    
    rp = RobotFileParser()
    rp.set_url(robots_txt_url)
    rp.read()

    return rp.can_fetch(user_agent, url)

def scrape_website(url):
    """
    Scrapes the given URL and returns the HTML content if scraping is allowed.
    """
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.prettify()  # Or any other parsing logic specific to your needs
    else:
        return None

def main():
    url_to_scrape = 'https://www.facebook.com/policies_center/'
    user_agent = 'MyWebScraper'
    
    # Check if allowed to scrape
    if is_allowed_to_scrape(url_to_scrape, user_agent):
        print(f"Scraping is allowed by robots.txt for {url_to_scrape}")
        content = scrape_website(url_to_scrape)
        if content:
            print("Scraped content successfully:")
        else:
            print("Failed to scrape the content.")
    else:
        print(f"Scraping is not allowed by robots.txt for {url_to_scrape}")

if __name__ == "__main__":
    main()
