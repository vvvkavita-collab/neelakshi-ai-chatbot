// ===============================
// Neelakshi AI Chatbot (Frontend)
// Gemini API compatible version
// ===============================

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const historyList = document.getElementById("history");

let history = [];
let chatHistory = [];

function appendMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.textContent = text;
  messageDiv.appendChild(bubble);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  userInput.value = "";
  userInput.style.height = "45px";

  // User message always role: user
  chatHistory.push({ role: "user", content: text });

  try {
    const response = await fetch("https://neelakshi-ai-chatbot.onrender.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistory }),
    });

    const data = await response.json();
    appendMessage("bot", data.reply);

    // Gemini expects bot replies to have role: model (NOT assistant)
    chatHistory.push({ role: "model", content: data.reply });

    saveToHistory(text, data.reply);
  } catch (error) {
    appendMessage("bot", "⚠️ Error: Unable to connect to server.");
  }
}

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

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});

sendBtn.addEventListener("click", sendMessage);
