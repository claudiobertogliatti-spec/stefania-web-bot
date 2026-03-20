import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)  # Permette a Systeme.io di comunicare con questo server

# Configurazione Anthropic
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Prompt di sistema per definire l'identità di Stefania
SYSTEM_PROMPT = """
Sei Stefania, la coordinatrice del team Evolution Pro. 
Il tuo obiettivo è assistere gli utenti con professionalità, empatia e precisione.
Sei pragmatica, orientata ai risultati e conosci perfettamente il sistema 'Main' gestito da Claudio e Antonella.
Usa un tono cordiale ma professionale.
"""

@app.route('/')
def home():
    return "Stefania Web Service is Online!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return jsonify({"response": response.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
