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

// ✅ Universal AI Assistant like ChatGPT
app.post("/api/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4.1-mini", // ✅ Free Tier Supported
        messages: [
          {
            role: "system",
            content:
              "You are a smart AI assistant. Answer in the same language as the user.",
          },
          { role: "user", content: userMessage },
        ],
        max_tokens: 800,
        temperature: 0.7,
      }),
    });

    const data = await response.json();
    const botReply =
      data.choices?.[0]?.message?.content || "Sorry, I couldn't understand.";

    res.json({ reply: botReply });
  } catch (error) {
    console.error("❌ Chat Error:", error);
    res.status(500).json({ reply: "⚠️ Server Error! Try later." });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`✅ Server running on PORT ${PORT}`));
