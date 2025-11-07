// ✅ backend/server.js
import express from "express";
import cors from "cors";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

app.post("/api/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;

    if (!OPENAI_API_KEY) {
      return res.status(500).json({ error: "OpenAI API Key Missing!" });
    }

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini", // ✅ Fast + accurate + low cost
        messages: [
          { role: "system", content: "You are a smart Indian AI Assistant. Answer accurately like ChatGPT." },
          { role: "user", content: userMessage }
        ]
      })
    });

    const data = await response.json();
    const botReply = data.choices?.[0]?.message?.content || "Sorry, I have no answer!";

    res.json({ answer: botReply });
  } catch (error) {
    console.error("Chat Error: ", error);
    res.status(500).json({ error: "Something went wrong!" });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`✅ Server running on PORT: ${PORT}`));
