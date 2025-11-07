const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

const API_BASE_URL = "https://neelakshi-ai-chatbot-1.onrender.com";

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  userInput.value = "";
  appendMessage("Typing...", "bot", true);

  try {
    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: message })
    });

    const data = await res.json();
    removeTypingIndicator();
    appendMessage(data.answer, "bot");
  } catch (err) {
    removeTypingIndicator();
    appendMessage("⚠️ Server error! Try later.", "bot");
    console.error(err);
  }
}

function appendMessage(text, type, temp = false) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", type);
  if (temp) msgDiv.id = "typing-indicator";

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.innerText = text;

  msgDiv.appendChild(bubble);
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
  const typing = document.getElementById("typing-indicator");
  if (typing) typing.remove();
}


