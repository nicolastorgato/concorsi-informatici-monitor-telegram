import requests
from bs4 import BeautifulSoup


website_url_root = "https://www.concorsipubblici.com"
website_url_list = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600/loc/veneto"

response = requests.get(website_url_list)

soup = BeautifulSoup(response.text, 'html.parser')

contenitore = soup.find("div", class_="views-rows")
bandi = contenitore.find_all('article', class_='node--type-contest')

for bando in bandi:
    titolo = bando.find('h2').text.strip()
    keywords = ["funzionario", "specialista"]
    if any(kw in titolo.lower() for kw in keywords):
        print(titolo + " - " + website_url_root + bando.find('a')['href'])