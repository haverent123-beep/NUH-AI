import os

from flask import Flask, request, jsonify, render_template
from openai import OpenAI

app = Flask(__name__)


def get_client():
    """Create an OpenAI client using a server-side environment variable."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=api_key)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a question."}), 400
    if len(message) > 10000:
        return jsonify({"error": "Your message is too long."}), 400

    try:
        client = get_client()
        result = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are NUH AI, a helpful all-topic assistant. "
                        "Support Telugu and English. Explain space, astronomy, "
                        "science, coding, education, history, technology, and recipes. "
                        "For Islam, Quran, Hadith, and Prophets, be respectful; "
                        "never invent verses or Hadith references, and clearly state "
                        "uncertainty. Explain difficult topics simply."
                    ),
                },
                {"role": "user", "content": message},
            ],
        )
        answer = result.choices[0].message.content
        return jsonify({"reply": answer or "No answer received."})

    except Exception:
        app.logger.exception("NUH AI chat request failed")
        return jsonify({
            "error": "AI request failed. Check API key, model access, and billing."
        }), 502


@app.route("/api/image", methods=["POST"])
def generate_image():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return jsonify({"error": "Please describe the image."}), 400
    if len(prompt) > 4000:
        return jsonify({"error": "Image prompt is too long."}), 400

    try:
        client = get_client()
        result = client.images.generate(
            model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
            prompt=prompt,
            size="1024x1024",
        )

        image_data = result.data[0].b64_json
        if not image_data:
            return jsonify({"error": "No image was returned."}), 502

        return jsonify({
            "image": "data:image/png;base64," + image_data
        })

    except Exception:
        app.logger.exception("NUH AI image request failed")
        return jsonify({
            "error": "Image generation failed. Check API access and billing."
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
