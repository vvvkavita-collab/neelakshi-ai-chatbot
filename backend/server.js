import express from "express";
import cors from "cors";
import fetch from "node-fetch";

const app = express();
app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("✅ Backend running...");
});

// ✅ This is the route Postman and frontend are calling
app.post("/api/chat", async (req, res) => {
  try {
    const { message } = req.body;

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: message }]
      })
    });

    const data = await response.json();
    console.log("OpenAI Response :", data);

    res.json({
      reply: data?.choices?.[0]?.message?.content || "⚠ No reply from OpenAI"
    });

  } catch (error) {
    console.error("❌ Backend Error:", error);
    res.status(500).json({ error: error.message || "Server failed" });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`✅ Backend running on PORT: ${PORT}`);
});

