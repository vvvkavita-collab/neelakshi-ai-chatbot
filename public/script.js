const backendURL = "https://neelakshi-ai-chatbot-api.onrender.com";

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

function addMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);
  messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const input = userInput.value.trim();
  if (!input) return;

  addMessage("You", input);
  userInput.value = "";

  const loading = document.createElement("div");
  loading.classList.add("message", "bot");
  loading.innerHTML = "<em>Thinking...</em>";
  chatBox.appendChild(loading);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await fetch(`${backendURL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    });

    const data = await res.json();
    loading.remove();

    addMessage("Bot", data.reply || "Sorry, I didn’t get that 😅");
  } catch (error) {
    loading.remove();
    addMessage("Bot", "⚠️ Error connecting to server!");
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
