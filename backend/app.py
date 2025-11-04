from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# ✅ Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment!")
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

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)

        return jsonify({"reply": response.text})
    except Exception as e:
        print("⚠️ Error in /chat:", e)
        return jsonify({"reply": f"⚠️ Error: {e}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
