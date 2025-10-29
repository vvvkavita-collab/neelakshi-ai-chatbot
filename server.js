// server.js
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import path from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { fileURLToPath } from "url";

dotenv.config();

// Fix __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// ✅ Root route
app.get("/", (req, res) => {
  res.send("<h2>✅ Gemini AI Server is running successfully!</h2>");
});

// ✅ Chat route
app.post("/chat", async (req, res) => {
  try {
    const userMessage = req.body.message;
    console.log("🟢 User:", userMessage);

    if (!userMessage) {
      return res.status(400).json({ error: "No message provided" });
    }

    // Use the latest stable model name:
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const result = await model.generateContent(userMessage);
    const reply = result.response.text();

    console.log("🤖 Gemini:", reply);
    res.json({ reply });
  } catch (error) {
    console.error("🔴 Error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});
