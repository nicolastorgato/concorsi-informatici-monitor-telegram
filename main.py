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

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
AI_MODELS = [
    "qwen/qwen3.6-plus:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    ]

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

def fetch_bando_details(bando_url):
    """Scrape la pagina del bando per estrarre dettagli come titolo, scadenza, requisiti."""
    response = requests.get(bando_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    testo_completo = soup.get_text(separator='\n', strip=True)
    return testo_completo

def load_profilo():
    """Carica il profilo utente da variabile d'ambiente."""
    profilo = os.environ.get('PROFILO')
    if not profilo:
        raise ValueError("Variabile d'ambiente PROFILO non configurata")
    return profilo

def read_ai_prompt():
    """Legge il prompt AI da un file di testo."""
    try:
        with open("ai_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("File ai_prompt.txt non trovato")

def ai_evaluate_bando(testo_bando, profilo):
    """Usa un modello AI per valutare se il bando è adatto al profilo dell'utente."""
    if not OPENROUTER_API_KEY:
        raise ValueError("Variabile d'ambiente OPENROUTER_API_KEY non configurata")
    ai_prompt = read_ai_prompt()
    prompt = ai_prompt.format(testo_bando=testo_bando, profilo=profilo)
    for model in AI_MODELS:
        try:
            print(f"➡️ Chiamata API a {model}...")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            response.raise_for_status()
            print(f"⬅️ Risposta da {model}")
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Errore con modello {model}: {e}, provo il prossimo...")
            continue

    return "⚠️ Valutazione AI non disponibile al momento."


# MAIN
def main():
    """Esegue il monitor: scarica i bandi, rileva i nuovi e invia le notifiche Telegram."""
    try:
        profilo = load_profilo()

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
                testo_bando = fetch_bando_details(url)
                valutazione = ai_evaluate_bando(testo_bando, profilo)
                messaggio = f"🆕 Nuovo bando trovato!\n\n🔗 {url}\n\n🤖 {valutazione}"
                send_message_to_telegram(messaggio)
        else:
            print("Nessun nuovo bando trovato.")

        save_seen_bandi(bandi_trovati)

    except Exception as e:
        send_message_to_telegram(f"⚠️ Errore nel monitor: {e}")


# Avvia lo script solo se eseguito direttamente, non se importato come modulo
if __name__ == "__main__": main()