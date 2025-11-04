const API_URL = "https://neelakshi-ai-chatbot-api.onrender.com/chat";

const chatBox = document.querySelector("#chat-box");
const userInput = document.querySelector("#user-input");
const sendBtn = document.querySelector("#send-btn");

function addMessage(sender, message) {
  const div = document.createElement("div");
  div.classList.add(sender);
  div.innerHTML = `<b>${sender === "bot" ? "Bot" : "You"}:</b> ${message}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const msg = userInput.value.trim();
  if (!msg) return;
  addMessage("user", msg);
  userInput.value = "";

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });

    const data = await res.json();
    addMessage("bot", data.reply || "⚠️ No response!");
  } catch (err) {
    addMessage("bot", "⚠️ Error connecting to server!");
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
