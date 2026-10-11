import os
import base64
import logging
from urllib.parse import quote

import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)  # Allows the Netlify frontend to call this Render backend.
logging.basicConfig(level=logging.INFO)


def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in Render Environment.")
    return genai.Client(api_key=api_key)


@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception:
        return jsonify({"service": "NUH AI API", "status": "running"})


@app.route("/health")
def health():
    return jsonify({"service": "NUH AI API", "status": "running"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a question."}), 400
    if len(message) > 10000:
        return jsonify({"error": "Your message is too long."}), 400

    try:
        client = get_gemini_client()
        model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash-lite")
        response = client.models.generate_content(
            model=model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are NUH AI, a helpful all-topic assistant. "
                    "Support Telugu and English. Explain science, coding, education, "
                    "history, technology, and recipes clearly. For Islam, Quran, "
                    "Hadith, and Prophets, be respectful; never invent verses or "
                    "Hadith references, and clearly state uncertainty."
                ),
                max_output_tokens=2048,
            ),
        )
        answer = response.text or "No answer received."
        return jsonify({"reply": answer})

    except Exception as exc:
        app.logger.exception("NUH AI Gemini chat request failed")
        return jsonify({
            "error": "Free chat request failed. Check GEMINI_API_KEY, model availability, or free-tier limits.",
            "details": str(exc)[:300],
        }), 502


@app.route("/api/image", methods=["POST"])
def generate_image():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return jsonify({"error": "Please describe the image."}), 400
    if len(prompt) > 4000:
        return jsonify({"error": "Image prompt is too long."}), 400

    # Pollinations currently requires an API key for generation.
    # Keep it server-side; never put it in the frontend.
    api_key = os.environ.get("POLLINATIONS_API_KEY")
    if not api_key:
        return jsonify({
            "error": "Image generation is not configured yet. Add POLLINATIONS_API_KEY in Render Environment. Check the provider's current free usage and limits before using it."
        }), 503

    try:
        model = os.getenv("POLLINATIONS_IMAGE_MODEL", "flux")
        url = "https://gen.pollinations.ai/image/" + quote(prompt, safe="")
        response = requests.get(
            url,
            params={"model": model, "width": 1024, "height": 1024},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            raise RuntimeError("Image provider returned a non-image response.")
        encoded = base64.b64encode(response.content).decode("ascii")
        return jsonify({"image": f"data:{content_type};base64,{encoded}"})

    except Exception as exc:
        app.logger.exception("NUH AI image request failed")
        return jsonify({
            "error": "Image generation failed. Check Pollinations key, model availability, and current usage limits.",
            "details": str(exc)[:300],
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
