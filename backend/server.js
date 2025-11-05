import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import path from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { fileURLToPath } from "url";
import fetch from "node-fetch";
import Parser from "rss-parser";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "../public")));

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const parser = new Parser();

// 🔹 Weather (location-aware)
async function getWeather(city = "Jaipur") {
  try {
    const geo = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1`);
    const geoData = await geo.json();

    if (!geoData.results || geoData.results.length === 0) {
      return `⚠️ क्षमा करें, "${city}" के लिए मौसम की जानकारी नहीं मिल सकी। कृपया सही शहर का नाम दें।`;
    }

    const { latitude, longitude, name, country } = geoData.results[0];
    const weather = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`);
    const weatherData = await weather.json();
    const { temperature, windspeed } = weatherData.current_weather;

    return `🌤️ ${name}, ${country} का तापमान ${temperature}°C है और हवा की गति ${windspeed} km/h है।`;
  } catch {
    return `⚠️ मौसम की जानकारी प्राप्त करने में त्रुटि हुई। कृपया बाद में प्रयास करें।`;
  }
}

// 🔹 News
async function getHindiNews() {
  try {
    const feed = await parser.parseURL("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi");
    return feed.items.slice(0, 5).map((item, i) => `${i + 1}. ${item.title}`);
  } catch {
    return ["❌ खबरें लोड नहीं हो सकीं।"];
  }
}

// 🔹 Gemini Prompt
function buildPrompt(userMessage) {
  const today = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  return `Today's date: ${today}
You are Neelakshi AI — a smart assistant that answers any question clearly and helpfully.

User asked: ${userMessage}

Please give a complete answer. If it's a how-to question, use numbered steps. If it's a factual query, give a short summary. If the user asked in Hindi, reply in Hindi. If in English, reply in English. Keep it clear, helpful, and no longer than 6 sentences.`;
}

// 🔹 Chat route
app.post("/chat", async (req, res) => {
  try {
    const userMessage = req.body.message?.trim();
    if (!userMessage) return res.status(400).json({ error: "No message provided" });

    const lower = userMessage.toLowerCase();

    // 🔹 Hardcoded reply for Collector
    if (
      lower.includes("collector") ||
      lower.includes("कलेक्टर") ||
      lower.includes("जिला अधिकारी") ||
      lower.includes("district magistrate")
    ) {
      return res.json({
        reply: "🧑‍💼 जयपुर के वर्तमान कलेक्टर हैं डॉ. जितेन्द्र कुमार सोनी (IAS 2010 बैच)।"
      });
    }

    // 🔹 Hindi News
    if (["news", "खबर", "समाचार", "headline"].some(w => lower.includes(w))) {
      const headlines = await getHindiNews();
      return res.json({ reply: `🗞️ आज की टॉप हिंदी खबरें:\n\n${headlines.join("\n")}` });
    }

    // 🔹 Weather
    if (lower.includes("weather") || lower.includes("मौसम")) {
      const city = lower.replace("weather", "").replace("मौसम", "").trim() || "Jaipur";
      const weather = await getWeather(city);
      return res.json({ reply: weather });
    }

    // 🔹 Gemini AI reply
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    const result = await model.generateContent(buildPrompt(userMessage));
    const reply = result.response.text();
    return res.json({ reply });

  } catch (error) {
    console.error("🔴 Error:", error);
    return res.status(500).json({
      reply: "⚠️ Sorry, I couldn't fetch a live response. Example: The current Collector of Jaipur is Dr. Jitendra Kumar Soni (IAS 2010 batch)."
    });
  }
});

// 🔹 Ping route for testing
app.get("/ping", (req, res) => {
  res.json({ message: "pong" });
});

app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});
