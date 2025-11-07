const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// ✅ Update: Correct Backend Endpoint
const API_BASE_URL = "https://neelakshi-backend.onrender.com";

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    userInput.value = "";

    appendMessage("Typing...", "bot", true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        removeTypingIndicator();
        appendMessage(data.reply, "bot");

    } catch (error) {
        removeTypingIndicator();
        appendMessage("⚠️ Server error! Try later.", "bot");
        console.error(error);
    }
}
