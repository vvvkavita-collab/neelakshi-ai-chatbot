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

const app = express(); // ✅ app is defined here
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "../public")));

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const parser = new Parser();

// ✅ Now add your /chat route BELOW this line
app.post("/chat", async (req, res) => {
  // your route logic here...
});
