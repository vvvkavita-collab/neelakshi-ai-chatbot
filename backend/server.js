import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

app.post("/api/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;

    if (!userMessage) {
      return res.json({ reply: "Please ask something." });
    }

    const response = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: "You are Neelakshi AI: a smart, updated Indian AI assistant. Give accurate responses like ChatGPT."
        },
        { role: "user", content: userMessage }
      ]
    });

    res.json({ reply: response.choices[0].message.content });
  } catch (error) {
    console.error("❌ Backend Error:", error);
    res.status(500).json({ reply: "⚠️ Error! Please try again later." });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`✅ Backend running on PORT: ${PORT}`));
