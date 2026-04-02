import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from main import ai_evaluate_bando

testo_bando = """
Comune di Treviso - Concorso pubblico per 1 posto di Funzionario Informatico.
Requisiti: laurea in informatica o discipline scientifiche.
Competenze richieste: gestione reti, sviluppo web, PHP, Python.
Sede di lavoro: Treviso.
Contratto: tempo indeterminato.
Scadenza: 30/04/2026.
"""

profilo = "Laureato in Scienze Multimediali, competenze PHP Laravel Python, abito a Treviso, cerco tempo indeterminato"

risultato = ai_evaluate_bando(testo_bando, profilo)
print(risultato)