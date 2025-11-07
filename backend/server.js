import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import OpenAI from "openai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

app.post("/api/chat", async (req, res) => {
  const { message } = req.body;

  try {
    const response = await client.chat.completions.create({
      model: "gpt-4o-mini", // ✅ Always available on free tier
      messages: [
        {
          role: "system",
          content:
            "You are Neelakshi AI, a smart, helpful Jaipur-based assistant answering in Hindi or English depending on user language.",
        },
        { role: "user", content: message },
      ],
      temperature: 0.7,
    });

    const reply = response.choices?.[0]?.message?.content || "No reply";
    res.json({ reply });
  } catch (error) {
    console.error("🔥 API ERROR:", error?.response?.data || error.message);
    res.status(500).json({
      reply: "⚠️ Server Error! Try later",
      error: error?.response?.data || error.message,
    });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () =>
  console.log(`✅ Neelakshi AI Server running on PORT ${PORT}`)
);
