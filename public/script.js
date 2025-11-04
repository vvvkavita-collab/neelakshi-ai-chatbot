document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("user-input").addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessage();
});

async function sendMessage() {
  const userInput = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");
  const userMessage = userInput.value.trim();

  if (userMessage === "") return;

  chatBox.innerHTML += `<div class="message user"><strong>You:</strong> ${userMessage}</div>`;
  userInput.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch("https://neelakshi-ai-chatbot-api.onrender.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });

    const data = await response.json();
    chatBox.innerHTML += `<div class="message bot"><strong>Bot:</strong> ${data.reply}</div>`;
  } catch (error) {
    chatBox.innerHTML += `<div class="message bot error"><strong>Bot:</strong> ⚠️ Error connecting to server!</div>`;
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}
