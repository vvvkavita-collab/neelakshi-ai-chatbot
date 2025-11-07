const express = require("express");
const axios = require("axios");
const { Configuration, OpenAIApi } = require("openai");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});

const openai = new OpenAIApi(configuration);

// Example: Simple web search function using SerpAPI (or any API)
async function webSearch(query) {
  try {
    // Example using a free web search API (replace with actual API)
    const response = await axios.get("https://serpapi.com/search.json", {
      params: {
        q: query,
        api_key: "YOUR_SERPAPI_KEY", // You need to sign up
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

app.post("/ask", async (req, res) => {
  const { question } = req.body;

  try {
    // Step 1: Try web search for current info
    const searchResult = await webSearch(question);

    let prompt = "";
    if (searchResult) {
      // Give GPT the snippet from web search to answer accurately
      prompt = `Answer the following question using this information: "${searchResult}"\nQuestion: ${question}`;
    } else {
      // Use GPT only if no web info found
      prompt = `Answer this question accurately: ${question}`;
    }

    const completion = await openai.createChatCompletion({
      model: "gpt-4o-mini", // Can also use GPT-4-turbo if you have
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

app.listen(process.env.PORT || 10000, () => {
  console.log(`Server running on port ${process.env.PORT}`);
});
