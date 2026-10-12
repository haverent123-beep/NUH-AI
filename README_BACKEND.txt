NUH AI BACKEND (Render)

Files:
- app.py
- requirements.txt

Render settings:
- Build command: pip install -r requirements.txt
- Start command: gunicorn app:app

Environment variables (Render -> Environment):
- GEMINI_API_KEY = your Gemini API key (required for chat)
- POLLINATIONS_API_KEY = your Pollinations API key (required for image generation)
- Optional: GEMINI_CHAT_MODEL (default gemini-2.5-flash-lite)
- Optional: POLLINATIONS_IMAGE_MODEL (default flux)
- Optional: POLLINATIONS_EDIT_MODEL (default kontext; requires provider support for image edits)

Do not put these keys in Netlify/frontend JavaScript. After deploy, test https://YOUR-BACKEND/health. Frontend default backend URL is https://nuh-ai.onrender.com.

Provider availability, valid API keys, account balance/budget and rate limits can affect image generation.
