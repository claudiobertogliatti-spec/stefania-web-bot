#!/usr/bin/env python3
"""
STEFANIA TELEGRAM — Bot Telegram di Evolution PRO
Usa lo stesso system prompt di STEFANIA WEB (stefania_web.py).
Deploy su Render.com come servizio separato (Background Worker).

Variabili d'ambiente richieste su Render:
  TELEGRAM_TOKEN      — token del bot (da @BotFather)
  ANTHROPIC_API_KEY   — chiave API Anthropic
  STEFANIA_WEB_MODEL  — opzionale, default: claude-haiku-4-5-20251001
"""

import os
import logging
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

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import anthropic

# ── Importa system prompt e builder da stefania_web ────────────────────────────
# Se i due file sono nella stessa directory su Render, questo import funziona.
# In alternativa, copia qui SYSTEM_BASE e build_system per renderlo autonomo.
try:
    from stefania_web import build_system, MODEL
except ImportError:
    # Fallback: definisci il modello e un builder minimale se stefania_web
    # non è raggiungibile. Sostituisci con il prompt completo se necessario.
    MODEL = os.environ.get("STEFANIA_WEB_MODEL", "claude-haiku-4-5-20251001")

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
NO  - non adatto: e' un dipendente, sta ancora cercando clienti, fa MLM,
      fa trading, non ha ancora un metodo che funziona con clienti veri
Se non e' adatto, digli la verita': "In questo momento non sei nel profilo
giusto per Evolution PRO. Il sistema funziona per chi ha gia' clienti
e un metodo che da' risultati."

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

    def build_system(page: str) -> str:
        contexts = {
            "telegram": "Il visitatore arriva da Telegram. Potrebbe essere un lead freddo o qualcuno che ha sentito parlare di Evolution PRO. Qualificalo con una domanda semplice su cosa fa nella vita.",
            "default": "Canale generico.",
        }
        ctx = contexts.get(page, contexts["default"])
        return SYSTEM_BASE + f"\n\nCONTESTO CANALE: {ctx}"


# ── Setup ───────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MAX_HISTORY = 20  # messaggi per utente, stesso limite del web

# Memoria conversazioni: { chat_id: [{"role": ..., "content": ...}, ...] }
conversations: dict[int, list[dict]] = {}


# ── Helpers ─────────────────────────────────────────────────────────────────────
def get_history(chat_id: int) -> list[dict]:
    return conversations.setdefault(chat_id, [])


def trim_history(chat_id: int) -> None:
    hist = conversations.get(chat_id, [])
    if len(hist) > MAX_HISTORY:
        conversations[chat_id] = hist[-MAX_HISTORY:]


def call_claude(messages: list[dict]) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=build_system("telegram"),
        messages=messages,
    )
    return next((b.text for b in resp.content if b.type == "text"), "")


# ── Command handlers ─────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start — azzera la conversazione e invia il messaggio di benvenuto.
    """
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    await update.message.reply_text(
        "Ciao! Sono Stefania.\nDi cosa ti occupi di preciso?"
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /reset — cancella la cronologia e riparte dall'inizio.
    """
    chat_id = update.effective_chat.id
    conversations[chat_id] = []
    await update.message.reply_text(
        "Cronologia azzerata. Ripartiamo da capo.\nDi cosa ti occupi di preciso?"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Sono Stefania, assistente di Evolution PRO.\n\n"
        "/start — inizia una nuova conversazione\n"
        "/reset — azzera la cronologia\n\n"
        "Scrivimi pure un messaggio per iniziare."
    )


# ── Message handler ──────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.effective_chat.id
    user_txt = (update.message.text or "").strip()

    if not user_txt:
        return

    if not ANTHROPIC_API_KEY:
        await update.message.reply_text(
            "Servizio non disponibile al momento. Scrivi a claudio@evolution-pro.it"
        )
        return

    # Aggiunge il messaggio utente alla storia
    history = get_history(chat_id)
    history.append({"role": "user", "content": user_txt})
    trim_history(chat_id)

    # Indicatore di digitazione
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        reply = call_claude(history)
        history.append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except anthropic.AuthenticationError:
        logger.error("Anthropic AuthenticationError")
        await update.message.reply_text(
            "Servizio non disponibile. Scrivi a claudio@evolution-pro.it"
        )
    except anthropic.RateLimitError:
        logger.warning("Anthropic RateLimitError")
        await update.message.reply_text(
            "Troppo traffico in questo momento. Riprova tra qualche secondo."
        )
    except Exception as e:
        logger.error(f"handle_message error: {e}")
        await update.message.reply_text(
            "Errore tecnico. Scrivi a claudio@evolution-pro.it"
        )


# ── Entrypoint ───────────────────────────────────────────────────────────────────
def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "TELEGRAM_TOKEN non configurato. "
            "Aggiungila nelle variabili d'ambiente di Render."
        )
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY non configurata — le risposte AI non funzioneranno.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info(f"Stefania Telegram avviata — modello: {MODEL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
