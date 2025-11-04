// public/script.js
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// When frontend is served from same backend, just use relative path:
const API_BASE = ""; // empty => same origin
const CHAT_ENDPOINT = API_BASE + "/chat";

function addMessageBubble(role, text) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message", role);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setThinking() {
  addMessageBubble("bot", "⏳ Thinking...");
}

function updateLastBotMessage(text) {
  const botMessages = chatBox.querySelectorAll(".message.bot .bubble");
  if (botMessages.length > 0) {
    botMessages[botMessages.length - 1].textContent = text;
  }
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessageBubble("user", message);
  userInput.value = "";
  setThinking();

  try {
    const res = await fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: [{ role: "user", content: message }] }),
    });

    if (!res.ok) {
      const err = await res.text();
      updateLastBotMessage("⚠️ Server error");
      console.error("Server error:", err);
      return;
    }

    const data = await res.json();
    updateLastBotMessage(data.reply || "⚠️ No reply");
  } catch (err) {
    console.error("Network error:", err);
    updateLastBotMessage("❌ Error connecting to server.");
  }
}

// events
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

