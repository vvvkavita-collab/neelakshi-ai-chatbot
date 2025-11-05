const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// ⚡ Update your Render backend URL here
const API_BASE_URL = "https://neelakshi-ai-chatbot.onrender.com";

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    userInput.value = "";

    appendMessage("Typing...", "bot", true);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }) // ✅ matches backend
        });

        if (!response.ok) throw new Error(`Server Error: ${response.status}`);

        const data = await response.json();
        removeTypingIndicator();
        appendMessage(data.reply || "No response received", "bot");

    } catch (error) {
        removeTypingIndicator();
        appendMessage("⚠️ Server Connection Error! Try again later.", "bot");
        console.error("Error in Chat:", error);
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

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
    const typingMsg = document.querySelector(".message.typing");
    if (typingMsg) typingMsg.remove();
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
