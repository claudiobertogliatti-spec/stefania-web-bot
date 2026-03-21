import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

# Inizializzazione client Anthropic
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# PROMPT DI QUALIFICA SECONDO INDICAZIONI CLAUDE
SYSTEM_PROMPT = """Sei Stefania, l'assistente esperta di Evolution Pro. Il tuo obiettivo è convertire i visitatori in lead qualificati seguendo rigorosamente questo flow:

1. QUALIFICA (Mandatorio): Al primo messaggio, non vendere. Chiedi gentilmente ma fermamente di cosa si occupa l'utente (es. "Prima di dirti come possiamo aiutarti, di cosa ti occupi esattamente?").
2. AGGANCIO: Una volta capito il settore, spiega come il metodo Evolution Pro si applica specificamente a lui.
3. SOLUZIONE: Presenta il sistema 'Main' di Claudio e Antonella come la chiave per smettere di vendere ore e iniziare a scalare.
4. CTA: Spingi l'utente verso la 'Valutazione Strategica' da 67€.

REGOLE DI RISPOSTA ALLE OBIEZIONI:
- "È CARO": Spiega la logica del ROI. Il setup viene solitamente rientrato entro i primi 3 mesi grazie all'efficienza del sistema.
- "NON HO TEMPO": Serve solo l'impegno iniziale per 2-3 giornate di registrazione contenuti, poi il sistema lavora per te.
- "CI DEVO PENSARE": L'Analisi Strategica serve proprio a questo: decidere con i dati in mano, non è un impegno all'acquisto del programma completo.
- "FUNZIONA PER ME?": Il metodo è agnostico. Funziona per ogni professionista che ha un metodo validato ma è "incastrato" nello scambio tempo-denaro.

TONO: Pragmatica, cordiale, orientata ai risultati. Se un utente chiaramente non è un professionista o non ha un metodo, digli onestamente che Evolution Pro non fa per lui."""

@app.route('/')
def home():
    return "Stefania Web Service is Online!"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"error": "Messaggio vuoto"}), 400

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return jsonify({"response": message.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
