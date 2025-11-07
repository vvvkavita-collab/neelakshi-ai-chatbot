const API_BASE_URL = "https://neelakshi-ai-chatbot.onrender.com"; // your Render URL

const response = await fetch(`${API_BASE_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message })
});
const data = await response.json();
appendMessage(data.answer || "⚠️ No reply received", "bot");
