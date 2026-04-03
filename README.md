# 🤖 Concorsi Informatici Monitor — Notifiche Telegram per bandi PA in Veneto
🔍 Script che permette di monitorare i bandi di concorso pubblico per i profili di funzionario / specialista informatico nella Regione Veneto (presenti sul portale [concorsipubblici.com](https://www.concorsipubblici.com)). Permette di ricevere notifiche giornaliere via Telegram con l'elenco dei nuovi concorsi disponibili e la relativa valutazione AI di allineamento con il proprio profilo lavorativo.

---

## ✨ Funzionalità

- 🔍 Monitora ogni giorno i nuovi bandi di concorso per profili informatici
- 🤖 Valuta automaticamente ogni bando tramite AI (OpenRouter) in base al tuo profilo
- 📩 Invia notifiche su Telegram solo per i bandi nuovi
- 💾 Ricorda i bandi già notificati per evitare duplicati
- ⚙️ Completamente automatizzato con GitHub Actions — zero intervento manuale
- 💸 100% gratuito

---

## 🏗️ Come funziona

```
GitHub Actions (ogni giorno alle 08:00)
        ↓
Scraping di concorsipubblici.com
        ↓
Filtra i bandi per keyword (funzionario, specialista...)
        ↓
Confronta con i bandi già visti (seen_bandi.json)
        ↓
Per ogni bando nuovo → valutazione AI con il tuo profilo
        ↓
Notifica Telegram con link e valutazione
```

---

## 🚀 Setup

### 1. Fai fork del repository

Clicca su **Fork** in alto a destra su GitHub per creare una copia del progetto nel tuo account.

### 2. Crea un Bot Telegram

1. Apri Telegram e cerca **@BotFather**
2. Scrivi `/newbot` e segui le istruzioni
3. Salva il **token** che ti viene fornito
4. Manda un messaggio al tuo bot, poi vai su:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. Trova e salva il tuo **Chat ID** nel campo `"chat": {"id": ...}`

### 3. Crea un account OpenRouter

1. Vai su [openrouter.ai](https://openrouter.ai) e crea un account
2. Vai in **Keys → Create Key**
3. Salva la chiave API

### 4. Configura i Secrets su GitHub

Vai in **Settings → Secrets and variables → Actions** del tuo fork e aggiungi:

| Nome | Valore |
|------|--------|
| `TELEGRAM_TOKEN` | Il token del tuo bot Telegram |
| `TELEGRAM_CHAT_ID` | Il tuo Chat ID numerico |
| `OPENROUTER_API_KEY` | La tua chiave API di OpenRouter |
| `PROFILO` | Il tuo profilo professionale (vedi sezione sotto) |

### 5. Configura il tuo profilo

Il secret `PROFILO` deve contenere una descrizione del tuo profilo professionale. Esempio:

```
Laurea in Informatica, 5 anni di esperienza in PA, competenze PHP Laravel Python JavaScript.
Cerco posizioni a tempo indeterminato. Distanza massima accettabile: 40km da Treviso.
Preferisco enti locali o università.
```

Più è dettagliato, più la valutazione AI sarà accurata.

---

## ⚙️ Personalizzazione

### Cambiare le keyword di ricerca

Nel file `main.py` modifica la costante `KEYWORDS`:

```python
KEYWORDS = ["funzionario", "specialista", "istruttore", "sistemista"]
```

### Cambiare la regione o il settore

Modifica `WEBSITE_URL_LIST` in `main.py`:

```python
# Solo Lombardia
WEBSITE_URL_LIST = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600/loc/lombardia"

# Tutta Italia
WEBSITE_URL_LIST = "https://www.concorsipubblici.com/concorsi/occupazione/pro/settore-informatico-600"
```

### Cambiare l'orario di esecuzione

Nel file `.github/workflows/monitor.yml` modifica il cron:

```yaml
- cron: '0 7 * * *'  # ogni giorno alle 08:00 ora italiana (07:00 UTC)
```

Formato: `minuto ora * * *` — l'orario è in UTC (sottrai 1h in inverno, 2h in estate per l'ora italiana).

### Cambiare i modelli AI

In `main.py` modifica `AI_MODELS` — il primo è il preferito, gli altri sono fallback:

```python
AI_MODELS = [
    "qwen/qwen3.6-plus:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]
```

Trovi tutti i modelli gratuiti disponibili su [openrouter.ai/models](https://openrouter.ai/models) filtrando per **Free**.

---

## 🛠️ Installazione in locale

Se vuoi eseguire lo script in locale per testarlo:

```bash
# Clona il repository
git clone https://github.com/TUO_USERNAME/concorsi-informatici-monitor-telegram.git
cd concorsi-informatici-monitor-telegram

# Crea e attiva il virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows (Git Bash)
# oppure
source venv/bin/activate       # Mac/Linux

# Installa le dipendenze
pip install -r requirements.txt

# Crea il file .env
cp .env.example .env
# Modifica .env con le tue credenziali

# Esegui lo script
python main.py
```

### File .env

Crea un file `.env` nella root del progetto (non viene mai committato):

```
TELEGRAM_TOKEN=il_tuo_token
TELEGRAM_CHAT_ID=il_tuo_chat_id
OPENROUTER_API_KEY=la_tua_chiave
PROFILO=Il tuo profilo professionale qui
```

---

## 📁 Struttura del progetto

```
concorsi-informatici-monitor-telegram/
├── .github/
│   └── workflows/
│       └── monitor.yml       ← workflow GitHub Actions
├── tests/
│   └── test_ai.py            ← test della valutazione AI
├── .env.example              ← template per le variabili d'ambiente
├── .gitignore
├── main.py                   ← script principale
├── requirements.txt          ← dipendenze Python
└── seen_bandi.json           ← bandi già notificati (aggiornato automaticamente)
```

---

## 🧪 Test

Per testare solo la valutazione AI senza eseguire tutto lo script:

```bash
python tests/test_ai.py
```

---

## 📋 Requisiti

- Python 3.11+
- Account Telegram
- Account OpenRouter (gratuito)
- Account GitHub

---

## 🤝 Contributi

Pull request e issue sono benvenute! Se trovi un bug o hai un'idea per migliorare il progetto, apri una issue.

---

## 📄 Licenza

MIT — libero di usare, modificare e distribuire.
