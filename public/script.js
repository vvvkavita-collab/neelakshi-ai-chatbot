// ✅ frontend/script.js

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// ✅ Update with your Render URL only (already correct)
const API_BASE_URL = "https://neelakshi-ai-chatbot.onrender.com";

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

        appendMessage(data.answer || "⚠️ No reply received", "bot");

    } catch (error) {
        removeTypingIndicator();
        appendMessage("⚠️ Server Error! Try later", "bot");
        console.error(error);
    }
}

function appendMessage(message, sender, typing = false) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    if (typing) msgDiv.classList.add("typing");

    const bubbleDiv = document.createElement("div");
    bubbleDiv.classList.add("bubble");
    bubbleDiv.innerHTML = message;
    msgDiv.appendChild(bubbleDiv);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
    const typingMsg = document.querySelector(".message.typing");
    if (typingMsg) typingMsg.remove();
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
