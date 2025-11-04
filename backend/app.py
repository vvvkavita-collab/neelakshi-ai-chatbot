from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # allow frontend access

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Neelakshi AI Chatbot Backend is running!"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        # Simple AI logic (you can replace this with real AI or OpenAI API)
        if "hello" in user_message.lower():
            reply = "Hi Neelakshi! 👋 How are you today?"
        elif "jaipur collector" in user_message.lower():
            reply = "The current Jaipur Collector is Dr. Prakash Rajpurohit (IAS)."
        elif "your name" in user_message.lower():
            reply = "I'm Neelakshi AI, your smart chatbot assistant 🤖!"
        else:
            reply = "I'm not sure about that, but I’ll try to learn soon!"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
