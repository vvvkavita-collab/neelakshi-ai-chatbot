import express from "express";
import axios from "axios";
import OpenAI from "openai";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Web search via SerpAPI
async function webSearch(query) {
  try {
    const response = await axios.get("https://serpapi.com/search.json", {
      params: {
        q: query,
        api_key: process.env.SERPAPI_KEY,
      },
    });

    if (response.data.organic_results?.length > 0) {
      return response.data.organic_results[0].snippet;
    }
    return null;
  } catch (err) {
    console.error("Web search error:", err.message);
    return null;
  }
}

// Chat route
app.post("/ask", async (req, res) => {
  const { question } = req.body;
  if (!question) return res.status(400).json({ answer: "Please provide a question." });

  try {
    const snippet = await webSearch(question);
    const prompt = snippet
      ? `Using this information: "${snippet}", answer the question accurately.\nQuestion: ${question}`
      : `Answer this question accurately: ${question}`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are a helpful, accurate assistant." },
        { role: "user", content: prompt },
      ],
      temperature: 0.2,
      max_tokens: 500,
    });

    const answer = completion.choices[0].message.content;
    res.json({ answer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ answer: "Sorry, I could not find an answer." });
  }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
