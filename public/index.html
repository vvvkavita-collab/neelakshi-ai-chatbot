const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

const backendURL = "https://neelakshi-ai-chatbot-api.onrender.com";
// 👈 Replace this with your actual FastAPI backend URL from Render

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  userInput.value = "";

  addMessage("bot", "⏳ Thinking...");

  try {
    const response = await fetch(`${backendURL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: message }],
      }),
    });

    const data = await response.json();
    updateLastBotMessage(data.reply || "⚠️ No reply received.");
  } catch (error) {
    updateLastBotMessage("❌ Error connecting to server.");
    console.error(error);
  }
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.classList.add("message", role);
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function updateLastBotMessage(text) {
  const botMessages = chatBox.getElementsByClassName("bot");
  if (botMessages.length > 0) {
    botMessages[botMessages.length - 1].textContent = text;
  }
  chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
