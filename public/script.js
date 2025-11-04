// ==============================
// Neelakshi AI Chatbot - Frontend Script
// ==============================

// ✅ Change this link to your Render backend link:
const backendURL = "https://neelakshi-ai-chatbot-api.onrender.com";

// Select HTML elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Function to show messages in the chat
function addMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);
  messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight; // scroll to bottom
}

// Function to send user message to backend
async function sendMessage() {
  const input = userInput.value.trim();
  if (!input) return; // if empty input, do nothing

  addMessage("You", input);
  userInput.value = "";

  // Show typing message
  const loadingMessage = document.createElement("div");
  loadingMessage.classList.add("message", "bot");
  loadingMessage.innerHTML = "<em>Thinking...</em>";
  chatBox.appendChild(loadingMessage);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    // Send message to backend API
    const res = await fetch(`${backendURL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    });

    const data = await res.json();

    // Remove loading message
    loadingMessage.remove();

    // Show bot reply
    addMessage("Bot", data.reply || "Sorry, no reply received.");
  } catch (error) {
    loadingMessage.remove();
    addMessage("Bot", "⚠️ Error connecting to server!");
    console.error("Chat error:", error);
  }
}

// Event listeners
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});
