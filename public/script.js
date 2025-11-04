const API_URL = "https://neelakshi-ai-chatbot-api.onrender.com/chat"; // update if different

const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");

function appendMessage(sender, message, isBot = false) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", isBot ? "bot" : "user");
  msgDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;
  
  appendMessage("You", message);
  userInput.value = "";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    
    const data = await res.json();
    appendMessage("Bot", data.reply, true);
  } catch (error) {
    appendMessage("Bot", "⚠️ Error connecting to server!", true);
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
