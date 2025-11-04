from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

# Gemini API key (add in Render Environment tab)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"message": "✅ Neelakshi AI Chatbot Backend is Running!"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Please type something!"})

        # Use Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)

        return jsonify({"reply": response.text})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "⚠️ Error connecting to Gemini server!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
