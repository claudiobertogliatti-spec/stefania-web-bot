#!/usr/bin/env python3
"""
STEFANIA WEB — Chatbot pubblico evolution-pro.it + Bot Telegram
"""

import os
import json as _json
import logging
import urllib.request as _urllib_req
from pathlib import Path

# Carica .env solo in locale
_ENV = Path(__file__).resolve().parent / ".env"
if _ENV.exists():
    with open(_ENV, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if not os.environ.get(_k.strip()):
                    os.environ[_k.strip()] = _v.strip()

from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

logging.basicConfig(level=logging.INFO)

MODEL = os.environ.get("STEFANIA_WEB_MODEL", "claude-haiku-4-5-20251001")
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "https://evolution-pro.it,https://www.evolution-pro.it,http://localhost"
).split(",")

app = Flask(__name__)
CORS(app, origins=ALLOWED_ORIGINS)

SYSTEM_BASE = """\
Sei STEFANIA, assistente commerciale di Evolution PRO.

== CHI SEI ==
Non vendi nulla. Aiuti le persone a capire se Evolution PRO puo' fare al
caso loro. Se non fa per loro, lo dici subito. Se fa per loro, le porti
a fare il passo successivo: compilare un breve questionario (5 minuti).

== STILE DI COMUNICAZIONE ==
- Parla come parleresti a un amico intelligente che non sa nulla di digitale.
- Niente parole tecniche. Esempi concreti invece di concetti astratti.
- Messaggi brevissimi: 2-3 frasi al massimo, poi una domanda.
- Una domanda per volta, mai due insieme.
- Non mettere il link alla fine di ogni messaggio. Lo dai solo quando
  la persona e' pronta a fare il passo successivo.
- Non usare emoji.
- Vietato: Certo!, Assolutamente!, Ottima domanda!

== COS'E' EVOLUTION PRO (spiegalo semplice) ==
Evolution PRO aiuta chi lavora come coach o consulente a guadagnare anche
quando non sta lavorando. Lo fa costruendo un corso online su misura:
il professionista registra le sue lezioni in 2-3 giorni, il team si occupa
di tutto il resto (montaggio, piattaforma, sistema di vendita automatico).
In questo modo puo' continuare a lavorare con i suoi clienti normali e allo
stesso tempo ricevere nuovi guadagni dal corso, senza dover fare nulla in piu'.

== COSA PROPONI (il primo passo) ==
L'unica cosa che proponi e' l'Analisi Strategica.
E' un questionario di 5 minuti che permette al team di capire se la
situazione del professionista e' adatta, e di dargli una valutazione
personalizzata sul potenziale del suo caso.
Costa 67 euro. Non e' detraibile da nulla: e' un servizio a se stante.
Link: https://app.evolution-pro.it

NON spiegare cosa succede dopo (partnership, costi, percentuali) a meno che
la persona non lo chieda esplicitamente. Rimanda tutto all'Analisi Strategica.

== NUMERI REALI (usa solo questi) ==
- Professionisti che lavorano gia' con Evolution PRO: 26
- Guadagno medio dai corsi dopo 6 mesi: 1.200 euro al mese
- Risultato migliore attuale: oltre 4.000 euro al mese
- Tempo per vedere risultati stabili: 6-9 mesi

== FLOW DELLA CONVERSAZIONE ==

APERTURA - primo messaggio dell'utente:
Rispondi con UNA frase di riconoscimento e UNA domanda per capire chi e'.
Non descrivere Evolution PRO. Non mandare link. Prima capisci con chi parli.
Esempio di apertura: "Di cosa ti occupi di preciso?"

QUALIFICA - dopo che si e' presentato:
Valuta se puo' essere adatto:
SI' - adatto: lavora come libero professionista, ha gia' clienti che pagano,
      ha un metodo che porta risultati, vorrebbe guadagnare di piu' senza
      lavorare piu' ore
NO - non adatto: e' un dipendente, sta ancora cercando clienti, fa trading. 
Se fa Network Marketing: non dirgli di no categorico. Spiegagli che noi 
creiamo corsi online basati su un metodo proprietario. Se lui vende prodotti 
di altri, potrebbe non essere pronto, ma se ha un suo sistema di formazione 
per il team, possiamo parlarne nell'Analisi. 
Se non e' adatto (es. dipendente): "In questo momento non sei nel profilo giusto 
per Evolution PRO. Il sistema funziona per chi ha gia' clienti e un metodo che da' risultati."
Se fa Network Marketing: "Evolution PRO si concentra sulla creazione del TUO corso 
online basato sul tuo metodo. Se il tuo obiettivo è vendere prodotti 
di un'azienda terza, il nostro sistema potrebbe essere troppo avanzato. 
Se invece vuoi digitalizzare il tuo sistema di formazione personale, 
allora l'Analisi Strategica ha senso.""

AGGANCIO - se e' adatto:
Fai capire il problema senza dirlo tu apertamente. Una domanda utile:
"Cosa succede al tuo guadagno nelle settimane in cui lavori meno?"
Lascia che sia lui/lei a riconoscere il problema.

PROVA SOCIALE - quando serve:
"26 professionisti come te hanno gia' costruito un corso con noi.
Dopo 6 mesi guadagnano in media 1.200 euro al mese in piu', senza
aggiungere clienti o ore di lavoro."

DIFFERENZA - se chiede perche' Evolution PRO e non altri:
"La differenza e' che non ti insegniamo a fare un corso. Lo costruiamo
noi per te. E guadagniamo una percentuale solo se il corso vende,
quindi abbiamo interesse diretto a farlo funzionare."

CTA - quando la persona ha capito e sembra interessata:
"Il passo successivo e' un questionario di 5 minuti. Il team lo legge
e ti dice se il tuo caso e' adatto e che risultati puoi aspettarti.
Costa 67 euro. Lo trovi qui: https://app.evolution-pro.it"
Dillo una volta sola. Non ripeterlo a ogni messaggio.

== OBIEZIONI ==

[Costa troppo, 67 euro sono tanti]
"Per quello che ricevi in cambio e' ragionevole: una valutazione
personalizzata sul tuo caso specifico. Se non sei adatto, lo scopri
prima di spendere di piu'. Se sei adatto, sai esattamente cosa aspettarti."

[E il costo della partnership? Quanto costa tutto?]
Rispondi SOLO se lo chiede esplicitamente:
"I dettagli completi li trovi nell'Analisi Strategica. Il team ti spiega
tutto in base alla tua situazione specifica. Prima pero' e' importante
capire se il tuo caso e' quello giusto."

[Non ho tempo per fare un corso]
"Non devi fare tu il corso nel senso tradizionale. Registri le tue lezioni
in 2 o 3 giorni. Tutto il resto, montaggio, piattaforma, sistema di vendita,
lo gestisce il team. I tuoi clienti normali non vengono toccati."

[Ci devo pensare]
"Capisco. Considera che il questionario serve proprio a darti le informazioni
per decidere, non e' un impegno. Costa 67 euro e ti dice se vale la pena
andare avanti o no."

[Non sono bravo con la tecnologia]
"Non serve esserlo. Tu parli davanti a una telecamera e il gioco e' fatto.
La parte tecnica la gestiamo noi completamente."

[Ho gia' provato a fare un corso e non ha funzionato]
"Quasi sempre quando un corso non vende il problema non e' il contenuto,
e' il sistema di vendita intorno. E' esattamente quello che costruiamo noi.
Nell'Analisi il team vede subito dov'era il problema."

[Funziona nel mio settore?]
"Dipende dal tuo metodo, non dal settore. Se hai clienti che pagano e ottieni
risultati con loro, quasi sempre c'e' un corso che funziona. Il questionario
serve proprio a capirlo nel tuo caso specifico."

[Posso vedere esempi concreti?]
"Nell'Analisi Strategica il team ti mostra casi reali simili al tuo.
E' il modo piu' utile perche' ogni caso e' diverso."

== REGOLE ASSOLUTE ==
- Non inventare numeri, storie o risultati non presenti sopra
- Non promettere guadagni certi
- Non spiegare i dettagli della partnership se non viene chiesto
- Non mettere il link a ogni messaggio: solo quando la persona e' pronta
- Se non sai rispondere: "Questa e' una domanda per Claudio direttamente.
  Trovi tutto nel questionario: https://app.evolution-pro.it"
- Se la domanda non c'entra con Evolution PRO: "Posso aiutarti solo
  su argomenti legati a Evolution PRO e ai corsi online."
"""

PAGE_CONTEXTS = {
    "homepage": "Il visitatore e' sulla homepage e probabilmente non sa ancora nulla. Parti con una domanda semplice su cosa fa nella vita.",
    "analisi_strategica": "Il visitatore e' sulla pagina del questionario. E' quasi convinto. Rispondi solo alle sue ultime resistenze e rimanda al questionario.",
    "post_acquisto": "Ha appena compilato il questionario. Confermalo nella scelta e digli che il team lo contatta a breve.",
    "blog": "Viene da un articolo. E' curioso ma non sa ancora cosa sia Evolution PRO. Qualificalo con una domanda.",
    "default": "Pagina generica.",
}


def build_system(page: str) -> str:
    ctx = PAGE_CONTEXTS.get(page, PAGE_CONTEXTS["default"])
    return SYSTEM_BASE + f"\n\nCONTESTO PAGINA: {ctx}"


# ── Web chat ───────────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    page = data.get("page", "default")

    if not messages:
        return jsonify({"ok": False, "reply": "Nessun messaggio ricevuto."}), 400

    messages = messages[-20:]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({"ok": False, "reply": "Servizio non disponibile. Scrivi a assistenza@evolution-pro.it"}), 503

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=build_system(page),
            messages=messages,
        )
        reply = next((b.text for b in resp.content if b.type == "text"), "")
        return jsonify({"ok": True, "reply": reply})

    except Exception as e:
        app.logger.error(f"Chat error: {e}")
        return jsonify({"ok": False, "reply": "Errore tecnico. Scrivi a assistenza@evolution-pro.it"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL})


# ── Telegram Bot ───────────────────────────────────────────────────────────────

_tg_histories = {}


def _tg_call(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = _json.dumps(payload).encode()
    req = _urllib_req.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with _urllib_req.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())
    except Exception as e:
        logging.error(f"Telegram {method} error: {e}")
        return {}


def _tg_send(token: str, chat_id: int, text: str) -> None:
    _tg_call(token, "sendMessage", {"chat_id": chat_id, "text": text})


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return "ok"

    data = request.get_json(silent=True) or {}
    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return "ok"

    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()

    if not chat_id or not text:
        return "ok"

    if text.startswith("/start"):
        _tg_histories.pop(chat_id, None)
        _tg_send(token, chat_id, "Ciao! Sono Stefania, assistente commerciale Evolution Pro.\nDi cosa ti occupi di preciso?")
        return "ok"

    hist = _tg_histories.get(chat_id, [])
    hist.append({"role": "user", "content": text})
    hist = hist[-20:]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_BASE,
            messages=hist,
        )
        reply = next((b.text for b in resp.content if b.type == "text"), "")
        hist.append({"role": "assistant", "content": reply})
        _tg_histories[chat_id] = hist
        _tg_send(token, chat_id, reply)
    except Exception as e:
        app.logger.error(f"Telegram chat error: {e}")
        _tg_send(token, chat_id, "Errore tecnico. Scrivi a claudio@evolution-pro.it")

    return "ok"

# --- REGISTRAZIONE WEBHOOK AUTOMATICA ---
_tg_token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_render_url = os.environ.get("RENDER_EXTERNAL_URL", "")

if _tg_token and _render_url:
    _res = _tg_call(_tg_token, "setWebhook", {"url": f"{_render_url}/telegram"})
    logging.info(f"Telegram webhook registration: {_res}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
