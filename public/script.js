// script.js
const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// 🔹 Change this to your backend URL (no trailing slash)
const API_URL = "https://neelakshi-ai-chatbot.onrender.com/chat";

function addMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message");
  msg.innerHTML =
    `<strong>${sender}:</strong> ${text.replace(/\n/g, "<br>")}`;
  chatContainer.appendChild(msg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addMessage("You", text);
  userInput.value = "";
  addMessage("Bot", "⏳ Typing...");

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const data = await response.json();
    const reply = data.reply || "⚠️ No response from bot.";
    
    // Remove the "Typing..." message and add bot's reply
    chatContainer.lastChild.remove();
    addMessage("Bot", reply);

  } catch (error) {
    chatContainer.lastChild.remove();
    addMessage("Bot", "⚠️ Error connecting to server!");
    console.error("Chat error:", error);
  }
}

// ✅ When "Send" button is clicked
sendBtn.addEventListener("click", sendMessage);

// ✅ When "Enter" key is pressed
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
