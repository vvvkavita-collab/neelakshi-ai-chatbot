from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# Set your Gemini API key (use Render Environment Variable instead of hardcoding)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/')
def home():
    return jsonify({"message": "🤖 Neelakshi AI Chatbot API is running!"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)
        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"reply": f"⚠️ Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
