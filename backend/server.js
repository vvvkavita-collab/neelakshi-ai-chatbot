// ✅ backend/server.js
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

// ✅ Initialize OpenAI Client
const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.post("/api/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;

    const completion = await client.chat.completions.create({
      model: "gpt-4o-mini", // ✅ Fast + Accurate
      messages: [
        { role: "system", content: "You are a smart AI like ChatGPT. Answer accurately without location restrictions." },
        { role: "user", content: userMessage }
      ]
    });

    const botReply =
      completion.choices?.[0]?.message?.content ||
      "Sorry, I don't know this answer!";

    res.json({ answer: botReply });

  } catch (error) {
    console.error("Chat Error:", error.response?.data || error.message);
    res.status(500).json({ answer: "Server Error: Check Logs" });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`✅ Neelakshi AI Server running on PORT ${PORT}`));
