# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# Gemini + Google Programmable Search (live web)
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# Load environment variables from .env (locally). On Render, set these in Environment.
load_dotenv()

# --- Config / env vars (set these on Render or locally in .env) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")      # Google / Gemini API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")      # Google Programmable Search API key (same Google Cloud project)
GOOGLE_CX = os.getenv("GOOGLE_CX")                # Programmable Search Engine ID (cx)
# -----------------------------------------------------------------

# Validate keys early (optional)
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set.")
if not GOOGLE_API_KEY or not GOOGLE_CX:
    print("Warning: GOOGLE_API_KEY or GOOGLE_CX is not set. Live search will be disabled.")

# Configure Gemini client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow CORS from any origin (for now). Replace "*" with your static site URL for safety in production.
app.add_middleware(
   
