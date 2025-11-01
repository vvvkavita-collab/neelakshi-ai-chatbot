let history = [];
let chatHistory = [];

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  userInput.value = "";
  userInput.style.height = "45px";
  chatHistory.push({ role: "user", content: text });

  try {
    const response = await fetch("https://neelakshi-ai-chatbot.onrender.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistory }),
    });

    const data = await response.json();
    appendMessage("bot", data.reply);
    chatHistory.push({ role: "model", content: data.reply });

    saveToHistory(text, data.reply);
  } catch (error) {
    appendMessage("bot", "⚠️ Error: Unable to connect to server.");
  }
}
