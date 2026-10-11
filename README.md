# NUH AI Backend (separate)

Flask JSON API. Deploy this folder as a Render Web Service with:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`

Render environment variables:
- `OPENAI_API_KEY`: secret server-side key (never put this in frontend files)
- `FRONTEND_ORIGIN`: exact origin of deployed frontend, e.g. `https://your-site.onrender.com`
- Optional `OPENAI_CHAT_MODEL` (default `gpt-4o-mini`)
- Optional `OPENAI_IMAGE_MODEL` (default `gpt-image-1`)

After creating the backend service, update `window.NUH_AI_API_BASE` in frontend `index.html` to the new backend URL, redeploy frontend, then set `FRONTEND_ORIGIN` to the frontend URL. API root `/` returns a health JSON response.
