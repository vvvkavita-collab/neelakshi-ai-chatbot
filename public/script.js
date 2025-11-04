// script.js

// ✅ Use your actual backend URL
const API_BASE_URL = "https://neelakshi-ai-chatbot.onrender.com";

const chatContainer = document.getElementById("chat-container");
const inputField = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Add message to chat
function addMessage(sender, text, isBot = false) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message");
  msgDiv.classList.add(isBot ? "bot" : "user");
  msgDiv.innerHTML = `<b>${isBot ? "Bot" : "You"}:</b> ${text}`;
  chatContainer.appendChild(msgDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Send message to API
async function sendMessage() {
  const text = inputField.value.trim();
  if (!text) return;

  addMessage("You", text);
  inputField.value = "";

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    const data = await response.json();
    addMessage("Bot", data.reply || "⚠️ No reply from server.", true);
  } catch (err) {
    console.error("Chat error:", err);
    addMessage("Bot", "⚠️ Error connecting to server!", true);
  }
}

// Send message when clicking or pressing Enter
sendBtn.addEventListener("click", sendMessage);
inputField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

// Initial message
addMessage("Bot", "Hello Neelakshi 👋! How can I help you today?", true);
