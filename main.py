import requests
from bs4 import BeautifulSoup
import json


website_url_root = "https://www.concorsipubblici.com"
website_url_list = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600/loc/veneto"


try:
    with open("seen_bandi.json", "r") as f:
        bandi_visti = json.load(f)
except FileNotFoundError:
    bandi_visti = []  # prima volta, lista vuota


response = requests.get(website_url_list)

soup = BeautifulSoup(response.text, 'html.parser')

bandi_attivi_contenitore = soup.find("div", class_="views-rows")
bandi_attivi = bandi_attivi_contenitore.find_all('article', class_='node--type-contest')

bandi_trovati = []
for bando in bandi_attivi:
    titolo = bando.find('h2').text.strip()
    keywords = ["funzionario", "specialista"]
    if any(kw in titolo.lower() for kw in keywords):
        bando_url = website_url_root + bando.find('a')['href']
        bandi_trovati.append(bando_url)

bandi_nuovi = [url for url in bandi_trovati if url not in bandi_visti]

if bandi_nuovi:
    for url in bandi_nuovi:
        print(f"Nuovo bando trovato: {url}")
else:
    print("Nessun nuovo bando trovato.")

with open("seen_bandi.json", "w") as f:
    json.dump(bandi_trovati, f)
