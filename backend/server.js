import express from "express";
import axios from "axios";
import OpenAI from "openai";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Serve frontend files
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
app.use(express.static(path.join(__dirname, "frontend")));

// OpenAI client
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Web search using SerpAPI
async function webSearch(query) {
  try {
    const res = await axios.get("https://serpapi.com/search.json", {
      params: { q: query, api_key: process.env.SERPAPI_KEY }
    });
    return res.data.organic_results?.[0]?.snippet || null;
  } catch (err) {
    console.error("Web search error:", err.message);
    return null;
  }
}

// Chat endpoint
app.post("/ask", async (req, res) => {
  const { question } = req.body;
  if (!question) return res.status(400).json({ answer: "Please provide a question." });

  try {
    const snippet = await webSearch(question);
    const prompt = snippet
      ? `Using this info: "${snippet}", answer the question accurately.\nQuestion: ${question}`
      : `Answer accurately: ${question}`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: prompt }
      ],
      temperature: 0.2,
      max_tokens: 500
    });

    res.json({ answer: completion.choices[0].message.content });
  } catch (err) {
    console.error(err);
    res.status(500).json({ answer: "Sorry, I could not find an answer." });
  }
});

// Serve frontend for all other routes
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "frontend", "index.html"));
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
