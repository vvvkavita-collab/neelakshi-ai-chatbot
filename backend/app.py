from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# Set your Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "⚠️ Sorry, something went wrong!"}), 500


@app.route("/")
def home():
    return "Neelakshi AI Chatbot backend is running 💖"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
