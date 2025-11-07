import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// ✅ Correct OpenAI initialization
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// ✅ MAIN CHAT ROUTE ✅
app.post("/api/chat", async (req, res) => {
  try {
    const { message } = req.body;
    console.log("User Message Received:", message);

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: message }],
    });

    const reply =
      completion.choices[0]?.message?.content || "No reply received from OpenAI";

    console.log("AI Reply:", reply);

    res.json({ reply }); // ✅ Must return to frontend

  } catch (error) {
    console.error("Backend Error:", error);
    res.status(500).json({ error: error.message });
  }
});

// ✅ root test endpoint
app.get("/", (req, res) => {
  res.send("✅ Neelakshi AI Backend is Running!");
});

// ✅ PORT set for Render
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`));
