import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// ✅ FINAL FIX ✅
app.post("/api/chat", async (req, res) => {
  try {
    const { message } = req.body;
    console.log("User message:", message);

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: message }],
    });

    console.log("✅ OpenAI Response:", JSON.stringify(completion, null, 2));

    const reply = completion.choices[0]?.message?.content || "⚠️ No reply received";
    res.json({ reply });

  } catch (error) {
    console.error("⛔ Backend Error:", error);

    res.status(500).json({
      error: "Backend Error",
      details: error.message,
    });
  }
});

// ✅ Render PORT auto detect
const PORT = process.env.PORT || 10000;
app.listen(PORT, () =>
  console.log(`✅ Backend running on http://localhost:${PORT}`)
);
