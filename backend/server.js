// backend/server.js
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.post("/api/chat", async (req, res) => {
  try {
    const userMessage = req.body.message || "";

    if (!process.env.OPENAI_API_KEY) {
      return res.status(500).json({ error: "OPENAI_API_KEY not configured" });
    }

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are Neelakshi AI — a helpful assistant. Reply in the user's language (Hindi if user writes Hindi, else English). Keep answers clear and accurate."
        },
        { role: "user", content: userMessage }
      ],
      temperature: 0.7,
      max_tokens: 800
    });

    const reply = completion.choices?.[0]?.message?.content || "Sorry, I couldn't generate a reply.";
    return res.json({ answer: reply });
  } catch (err) {
    console.error("OpenAI error:", err?.response?.data || err?.message || err);
    return res.status(500).json({ error: "Server Error", details: err?.message || err });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`✅ Server running on PORT ${PORT}`));
