const express = require("express");
const axios = require("axios");
const { Configuration, OpenAIApi } = require("openai");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

// OpenAI configuration
const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

// Web search function using SerpAPI
async function webSearch(query) {
  try {
    const response = await axios.get("https://serpapi.com/search.json", {
      params: {
        q: query,
        api_key: process.env.SERPAPI_KEY,
      },
    });

    if (response.data.organic_results && response.data.organic_results.length > 0) {
      return response.data.organic_results[0].snippet;
    }
    return null;
  } catch (err) {
    console.log("Web search error:", err.message);
    return null;
  }
}

// Chat route
app.post("/ask", async (req, res) => {
  const { question } = req.body;

  if (!question) {
    return res.status(400).json({ answer: "Please provide a question." });
  }

  try {
    // Step 1: Try web search
    const searchResult = await webSearch(question);

    let prompt = "";
    if (searchResult) {
      prompt = `Using this information: "${searchResult}", answer the question accurately.\nQuestion: ${question}`;
    } else {
      prompt = `Answer this question accurately: ${question}`;
    }

    // Step 2: GPT completion
    const completion = await openai.createChatCompletion({
      model: "gpt-4o-mini",  // or "gpt-4-turbo" if available
      messages: [
        { role: "system", content: "You are a helpful, accurate assistant." },
        { role: "user", content: prompt },
      ],
      temperature: 0.2,
      max_tokens: 500,
    });

    const answer = completion.data.choices[0].message.content;
    res.json({ answer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ answer: "Sorry, I could not find an answer." });
  }
});

// Start server
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
