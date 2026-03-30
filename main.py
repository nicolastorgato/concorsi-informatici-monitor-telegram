# IMPORTS
import os
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv


# CONFIGURATIONS
load_dotenv()

TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

SEEN_BANDI_FILE = "seen_bandi.json"

KEYWORDS = ["funzionario", "specialista"]

WEBSITE_URL_ROOT = "https://www.concorsipubblici.com"
WEBSITE_URL_LIST = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600/loc/veneto"

# FUNCTIONS
def load_seen_bandi():
    """Carica la lista dei bandi già visti da seen_bandi.json."""
    try:
        with open(SEEN_BANDI_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # prima volta, lista vuota

def save_seen_bandi(bandi):
    """Salva la lista dei bandi visti su seen_bandi.json."""
    with open(SEEN_BANDI_FILE, "w") as f:
        json.dump(bandi, f)

def scrape_bandi_attivi():
    """Scrape la pagina dei bandi attivi e restituisce una lista di elementi HTML dei bandi."""
    response = requests.get(WEBSITE_URL_LIST)
    response.raise_for_status()  # lancia eccezione se status != 200
    soup = BeautifulSoup(response.text, 'html.parser')
    bandi_attivi_contenitore = soup.find("div", class_="views-rows")
    return bandi_attivi_contenitore.find_all('article', class_='node--type-contest')

def send_message_to_telegram(message):
    """Invia un messaggio testuale al bot Telegram configurato."""
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    })

# MAIN
def main():
    """Esegue il monitor: scarica i bandi, rileva i nuovi e invia le notifiche Telegram."""
    try:

        bandi_visti = load_seen_bandi()

        bandi_attivi = scrape_bandi_attivi()

        bandi_trovati = []
        for bando in bandi_attivi:
            titolo = bando.find('h2').text.strip()
            if any(kw in titolo.lower() for kw in KEYWORDS):
                bando_url = WEBSITE_URL_ROOT + bando.find('a')['href']
                bandi_trovati.append(bando_url)

        bandi_nuovi = [url for url in bandi_trovati if url not in bandi_visti]

        if bandi_nuovi:
            for url in bandi_nuovi:
                print(f"Nuovo bando trovato: {url}")
                send_message_to_telegram(f"Nuovo bando trovato: {url}")
        else:
            print("Nessun nuovo bando trovato.")

        save_seen_bandi(bandi_trovati)

    except Exception as e:
        send_message_to_telegram(f"⚠️ Errore nel monitor: {e}")


# Avvia lo script solo se eseguito direttamente, non se importato come modulo
if __name__ == "__main__": main()