# IMPORTS
import os
import time
import random
from playwright.sync_api import sync_playwright
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
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]
SEEN_BANDI_FILE = "seen_bandi.json"
KEYWORDS = ["funzionario", "specialista"]
WEBSITE_URL_ROOT = "https://www.concorsipubblici.com"
WEBSITE_URL_LIST = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600/loc/veneto"

# ====================== FUNZIONI DI SCRAPING CON PLAYWRIGHT ======================

def scrape_with_playwright(url):
    """Usa Playwright per superare la protezione anti-robot"""
    print(f"🌐 Scraping con Playwright: {url}")
    
    with sync_playwright() as p:
        # Usa Chromium con fingerprint reali
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        # Context con fingerprint reali
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            locale='it-IT',
            timezone_id='Europe/Rome',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        )
        
        page = context.new_page()
        
        try:
            # Naviga con timeout più alto
            page.goto(url, timeout=30000, wait_until='networkidle')
            
            # Aspetta qualche secondo extra per far caricare tutto
            page.wait_for_timeout(3000)
            
            # Prende il contenuto HTML
            html = page.content()
            
            print(f"   ✓ Pagina caricata - Lunghezza: {len(html)} caratteri")
            
            browser.close()
            return html
            
        except Exception as e:
            print(f"   ❌ Errore Playwright: {e}")
            browser.close()
            raise

def scrape_bandi_attivi():
    """Scrape la pagina dei bandi attivi usando Playwright"""
    try:
        html = scrape_with_playwright(WEBSITE_URL_LIST)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Salva HTML per debug (opzionale)
        # with open("debug.html", "w", encoding="utf-8") as f:
        #     f.write(html)
        
        bandi_attivi_contenitore = soup.find("div", class_="views-rows")
        if not bandi_attivi_contenitore:
            print("⚠️  Non trovato div.views-rows - Provo selettore alternativo")
            bandi_attivi_contenitore = soup.find("div", {"class": "view-content"})
            
        if not bandi_attivi_contenitore:
            print("⚠️  Struttura pagina cambiata, salvo HTML per debug")
            with open("debug_error.html", "w", encoding="utf-8") as f:
                f.write(html[:2000])  # Salva inizio pagina per debug
            return []
        
        articoli = bandi_attivi_contenitore.find_all('article', class_='node--type-contest')
        print(f"   ✓ Trovati {len(articoli)} bandi nella lista")
        return articoli
        
    except Exception as e:
        print(f"❌ Errore in scrape_bandi_attivi: {e}")
        raise

def fetch_bando_details(bando_url):
    """Scrape la pagina dettagli di un singolo bando usando Playwright"""
    try:
        # Pausa casuale per sembrare più umano
        time.sleep(random.uniform(3, 6))
        
        html = scrape_with_playwright(bando_url)
        soup = BeautifulSoup(html, 'html.parser')
        testo_completo = soup.get_text(separator='\n', strip=True)
        
        print(f"   ✓ Dettagli scaricati - Lunghezza testo: {len(testo_completo)} caratteri")
        return testo_completo
        
    except Exception as e:
        print(f"❌ Errore in fetch_bando_details ({bando_url}): {e}")
        raise

# ====================== RESTO DELLE FUNZIONI ======================

def load_seen_bandi():
    """Carica la lista dei bandi già visti da seen_bandi.json."""
    try:
        with open(SEEN_BANDI_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_seen_bandi(bandi):
    """Salva la lista dei bandi visti su seen_bandi.json."""
    with open(SEEN_BANDI_FILE, "w") as f:
        json.dump(bandi, f)

def send_message_to_telegram(message):
    """Invia un messaggio testuale al bot Telegram configurato."""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

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
            titolo_element = bando.find('h2')
            if titolo_element:
                titolo = titolo_element.text.strip()
                if any(kw in titolo.lower() for kw in KEYWORDS):
                    link_element = bando.find('a')
                    if link_element and link_element.get('href'):
                        bando_url = WEBSITE_URL_ROOT + link_element['href']
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
        import traceback
        print(traceback.format_exc())
        send_message_to_telegram(f"⚠️ Errore nel monitor: {e}")

if __name__ == "__main__":
    main()