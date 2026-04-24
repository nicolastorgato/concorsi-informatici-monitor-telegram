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
    """Scrape la pagina dei bandi attivi - versione robusta"""
    try:
        html = scrape_with_playwright(WEBSITE_URL_LIST)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Metodo 1: Cerca il container view-content
        view_content = soup.find('div', class_='view-content')
        
        if view_content:
            articoli = view_content.find_all('article', class_='node--type-contest')
            print(f"   ✓ Trovati {len(articoli)} bandi nel view-content")
        else:
            # Metodo 2: Cerca direttamente tutti gli article
            articoli = soup.find_all('article', class_='node--type-contest')
            print(f"   ✓ Trovati {len(articoli)} bandi nella pagina")
        
        # Filtra solo quelli non scaduti (opzionale)
        # Puoi filtrare quelli che NON hanno la classe 'is-expired'
        bandi_attivi = []
        for art in articoli:
            if 'is-expired' not in art.get('class', []):
                bandi_attivi.append(art)
        
        if len(bandi_attivi) < len(articoli):
            print(f"   ✓ Filtrati {len(articoli) - len(bandi_attivi)} bandi scaduti")
        
        return bandi_attivi
        
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
            time.sleep(2)  # Aspetta 2 secondi prima del prossimo tentativo
            continue
    return "⚠️ Valutazione AI non disponibile al momento."

# MAIN
def main():
    """Esegue il monitor: scarica i bandi, rileva i nuovi e invia le notifiche Telegram."""
    try:
        print("🚀 Avvio monitor concorsi...")
        
        # Carica configurazioni
        profilo = load_profilo()
        print(f"✓ Profilo caricato: {profilo[:50]}...")
        
        # Carica bandi già visti
        bandi_visti = load_seen_bandi()
        print(f"✓ Bandi già visti: {len(bandi_visti)}")
        
        # Scrape bandi attivi
        print("🌐 Recupero bandi attivi...")
        bandi_attivi = scrape_bandi_attivi()
        
        if not bandi_attivi:
            print("⚠️ Nessun bando trovato nella pagina!")
            send_message_to_telegram("⚠️ Attenzione: Nessun bando trovato nella pagina. Potrebbe essere cambiata la struttura HTML.")
            return
        
        print(f"✓ Trovati {len(bandi_attivi)} bandi totali")
        
        # Filtra per keywords e estrai URL
        bandi_trovati = []
        for idx, bando in enumerate(bandi_attivi, 1):
            print(f"\n📌 Analizzo bando {idx}/{len(bandi_attivi)}")
            
            # Trova il titolo (h2 dentro l'article)
            titolo_element = bando.find('h2')
            if not titolo_element:
                print(f"   ⚠️ Nessun elemento titolo trovato")
                continue
                
            titolo = titolo_element.text.strip()
            print(f"   Titolo: {titolo[:100]}")
            
            # Verifica se contiene le keywords
            keyword_trovate = [kw for kw in KEYWORDS if kw in titolo.lower()]
            if keyword_trovate:
                print(f"   ✅ Match keyword: {keyword_trovate}")
                
                # Trova il link nell'elemento h2
                link_element = titolo_element.find('a')
                if not link_element or not link_element.get('href'):
                    print(f"   ⚠️ Nessun link trovato")
                    continue
                    
                href = link_element['href']
                
                # Costruisci URL completo
                if href.startswith('/'):
                    bando_url = WEBSITE_URL_ROOT + href
                else:
                    bando_url = href
                    
                bandi_trovati.append(bando_url)
                print(f"   ✅ URL aggiunto: {bando_url}")
            else:
                print(f"   ❌ Nessuna keyword match")
        
        print(f"\n📊 Riepilogo: {len(bandi_trovati)} bandi trovati con le keywords")
        
        # Identifica bandi nuovi
        bandi_nuovi = [url for url in bandi_trovati if url not in bandi_visti]
        print(f"🆕 Bandi nuovi: {len(bandi_nuovi)}")
        
        # Processa bandi nuovi
        if bandi_nuovi:
            for i, url in enumerate(bandi_nuovi, 1):
                print(f"\n📝 Processo bando nuovo {i}/{len(bandi_nuovi)}")
                print(f"   URL: {url}")
                
                try:
                    # Scarica dettagli del bando
                    print(f"   📥 Scarico dettagli...")
                    testo_bando = fetch_bando_details(url)
                    
                    # Valuta con AI
                    print(f"   🤖 Valutazione AI in corso...")
                    valutazione = ai_evaluate_bando(testo_bando, profilo)
                    
                    # Prepara messaggio
                    messaggio = f"🆕 Nuovo bando trovato!\n\n🔗 {url}\n\n🤖 {valutazione}"
                    
                    # Invia a Telegram
                    print(f"   📤 Invio a Telegram...")
                    send_message_to_telegram(messaggio)
                    
                    print(f"   ✅ Bando processato con successo")
                    
                except Exception as e:
                    print(f"   ❌ Errore processando bando {url}: {e}")
                    # Invia errore ma continua con gli altri bandi
                    send_message_to_telegram(f"⚠️ Errore processando bando: {url}\nErrore: {str(e)[:200]}")
                    continue
        else:
            print("\n✅ Nessun nuovo bando trovato.")
        
        # Salva la lista aggiornata dei bandi trovati
        save_seen_bandi(bandi_trovati)
        print(f"\n💾 Bandi salvati: {len(bandi_trovati)}")
        print("✅ Monitor completato con successo!")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ ERRORE CRITICO: {error_details}")
        
        # Invia notifica Telegram dell'errore
        try:
            send_message_to_telegram(f"⚠️ Errore critico nel monitor: {str(e)[:300]}")
        except:
            print("Impossibile inviare notifica errore a Telegram")
        
        raise  # Rilancia l'eccezione per debugging

if __name__ == "__main__":
    main()