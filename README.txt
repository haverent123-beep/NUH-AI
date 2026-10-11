# NUH AI backend — free-tier oriented setup

## What changed
- Chat now uses Google's Gemini API, default model `gemini-2.5-flash-lite`.
- Image generation uses Pollinations' current API.
- Keys are read from backend environment variables, not frontend code.
- `/api/chat` still returns `{ "reply": "..." }`.
- `/api/image` still returns `{ "image": "data:image/...;base64,..." }`.

## Important
Free-tier availability and quotas can change. Gemini chat has a free tier for eligible models/accounts, but rate limits apply. Pollinations currently requires an API key for generation; check its account page for current free usage/credits. Do not assume unlimited free image generation.

## Render settings
Build command (if needed): `pip install -r requirements.txt`
Start command: `gunicorn app:app`

Environment variables:
- `GEMINI_API_KEY` — create in Google AI Studio, keep secret in Render.
- `GEMINI_CHAT_MODEL` — optional; defaults to `gemini-2.5-flash-lite`.
- `POLLINATIONS_API_KEY` — create/check at https://enter.pollinations.ai, keep secret in Render.
- `POLLINATIONS_IMAGE_MODEL` — optional; defaults to `flux`.

Remove `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, and `OPENAI_IMAGE_MODEL` after verifying the new deployment works. Never paste secret keys into chat or commit them to GitHub.

## Frontend compatibility
The endpoints and response field names are preserved for the existing frontend. If the frontend hard-codes another backend URL, keep it pointing to the Render service URL.
