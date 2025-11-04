# Neelakshi AI Chatbot

## Run locally
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
uvicorn app:app --reload --host 0.0.0.0 --port 10000
Open http://localhost:10000 in browser.
