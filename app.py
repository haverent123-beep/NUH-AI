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
    """Generate from text, or edit an uploaded reference image."""
    api_key = os.environ.get("POLLINATIONS_API_KEY")
    if not api_key:
        return jsonify({
            "error": "Image generation is not configured. Add a valid POLLINATIONS_API_KEY in Render → Environment, then redeploy/restart the service."
        }), 503

    uploaded = request.files.get("image")
    if uploaded:
        prompt = str(request.form.get("prompt", "")).strip()
    else:
        data = request.get_json(silent=True) or {}
        prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return jsonify({"error": "Please describe the image or how you want to edit it."}), 400
    if len(prompt) > 4000:
        return jsonify({"error": "Image prompt is too long (maximum 4000 characters)."}), 400

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        if uploaded:
            if uploaded.mimetype not in ("image/jpeg", "image/png", "image/webp"):
                return jsonify({"error": "Upload a PNG, JPG, or WebP image."}), 400
            image_bytes = uploaded.read(8 * 1024 * 1024 + 1)
            if not image_bytes:
                return jsonify({"error": "The uploaded image is empty."}), 400
            if len(image_bytes) > 8 * 1024 * 1024:
                return jsonify({"error": "Image is too large. Maximum upload size is 8 MB."}), 413
            # Pollinations OpenAI-compatible image editing endpoint.
            model = os.getenv("POLLINATIONS_EDIT_MODEL", "kontext")
            response = requests.post(
                "https://gen.pollinations.ai/v1/images/edits",
                headers=headers,
                data={"prompt": prompt, "model": model, "size": "1024x1024"},
                files={"image": (uploaded.filename or "reference-image.png", image_bytes, uploaded.mimetype)},
                timeout=180,
            )
            response.raise_for_status()
            payload = response.json()
            try:
                encoded = payload["data"][0]["b64_json"]
            except (KeyError, IndexError, TypeError):
                raise RuntimeError("Image editing provider did not return image data.")
            return jsonify({"image": f"data:image/png;base64,{encoded}", "mode": "edit"})

        model = os.getenv("POLLINATIONS_IMAGE_MODEL", "flux")
        url = "https://gen.pollinations.ai/image/" + quote(prompt, safe="")
        response = requests.get(
            url,
            params={"model": model, "width": 1024, "height": 1024},
            headers=headers,
            timeout=180,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            raise RuntimeError("Image provider returned a non-image response.")
        encoded = base64.b64encode(response.content).decode("ascii")
        return jsonify({"image": f"data:{content_type};base64,{encoded}", "mode": "generate"})

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        provider_detail = ""
        if exc.response is not None:
            provider_detail = exc.response.text[:250]
        app.logger.exception("NUH AI image provider returned HTTP error")
        if status == 401:
            message = "Pollinations API key is invalid. Update POLLINATIONS_API_KEY in Render Environment."
        elif status == 402:
            message = "Pollinations account/key has insufficient balance or budget for image generation. Check your provider account limits."
        elif status == 429:
            message = "Image generation rate limit reached. Wait a little and try again."
        else:
            message = f"Image provider request failed (HTTP {status}). Check the selected model and provider status."
        return jsonify({"error": message, "details": provider_detail}), 502
    except Exception as exc:
        app.logger.exception("NUH AI image request failed")
        return jsonify({
            "error": "Image request failed. Check the Pollinations key, model availability, and current usage limits.",
            "details": str(exc)[:300],
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
