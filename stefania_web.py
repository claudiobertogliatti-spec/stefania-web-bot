import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

# Inizializzazione corretta del client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

SYSTEM_PROMPT = """Sei Stefania, l'assistente esperta di Evolution Pro. 
Il tuo obiettivo è assistere gli utenti con professionalità, empatia e precisione.
Sei pragmatica, orientata ai risultati e conosci il sistema 'Main' di Claudio e Antonella."""

@app.route('/')
def home():
    return "Stefania Web Service is Online!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        # Sintassi specifica per l'ultima versione della libreria
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"response": message.content[0].text})
    except Exception as e:
        print(f"Errore API: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
