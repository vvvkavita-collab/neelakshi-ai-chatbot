// ===============================
// Neelakshi AI Chatbot (Frontend)
// ChatGPT-style UI
// ===============================

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const historyList = document.getElementById("history");

let history = [];

// Add message to chat
function appendMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  // Markdown-style formatting
  let html = text
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");

  bubble.innerHTML = html;
  messageDiv.appendChild(bubble);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Send message to backend
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  userInput.value = "";
  userInput.style.height = "45px"; // reset height

  try {
    const response = await fetch("https://neelakshi-ai-chatbot.onrender.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();
    appendMessage("bot", data.reply);
    saveToHistory(text, data.reply);
  } catch (error) {
    appendMessage("bot", "⚠️ Error: Unable to connect to server.");
  }
}

// Save chat history
function saveToHistory(userMsg, botMsg) {
  const entry = { userMsg, botMsg, time: new Date().toLocaleTimeString() };
  history.unshift(entry);
  updateHistory();
}

function updateHistory() {
  historyList.innerHTML = "";
  history.forEach((item, index) => {
    const li = document.createElement("li");
    li.textContent = `Chat ${index + 1}`;
    li.addEventListener("click", () => loadChat(index));
    historyList.appendChild(li);
  });
}

function loadChat(index) {
  const chat = history[index];
  chatBox.innerHTML = "";
  appendMessage("user", chat.userMsg);
  appendMessage("bot", chat.botMsg);
}

// Handle Enter/Shift+Enter
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Auto expand textarea
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});

sendBtn.addEventListener("click", sendMessage);
