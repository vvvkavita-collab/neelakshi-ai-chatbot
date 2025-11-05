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
      return res.json({ reply: weather || `⚠️ ${city} के मौसम की जानकारी नहीं मिल सकी।` });
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
