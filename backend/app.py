from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# --- Gemini API Key Setup ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in Render environment variables!")
else:
    print("✅ GEMINI_API_KEY loaded successfully.")
    genai.configure(api_key=api_key)


@app.route("/")
def home():
    return jsonify({"message": "✅ Neelakshi AI Chatbot Backend is Running!"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please type something!"})

        # Check if API key is configured before calling Gemini
        if not api_key:
            return jsonify({"reply": "⚠️ Gemini API key missing on server!"})

        # Initialize Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Generate response
        response = model.generate_content(user_message)

        return jsonify({"reply": response.text})

    except Exception as e:
        print("⚠️ Error in /chat:", e)
        return jsonify({"reply": "⚠️ Error connecting to Gemini server!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
