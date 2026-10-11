import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Configure FRONTEND_ORIGIN to your deployed frontend URL in Render.
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = os.getenv("FRONTEND_ORIGIN", "*")
    if allowed == "*" or origin == allowed:
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", methods=["GET"])
def health():
    return jsonify({"service": "NUH AI API", "status": "running"})

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Please enter a question."}), 400
    if len(message) > 10000:
        return jsonify({"error": "Your message is too long."}), 400
    try:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        client = OpenAI(api_key=key)
        result = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are NUH AI, a helpful assistant. Support Telugu and English. Be clear, accurate, and respectful."},
                {"role": "user", "content": message},
            ],
        )
        return jsonify({"reply": result.choices[0].message.content or "No answer received."})
    except Exception:
        app.logger.exception("NUH AI chat failed")
        return jsonify({"error": "AI request failed. Check server API key, model access, and billing."}), 502

@app.route("/api/image", methods=["POST", "OPTIONS"])
def image():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "Please describe the image."}), 400
    if len(prompt) > 4000:
        return jsonify({"error": "Image prompt is too long."}), 400
    try:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        client = OpenAI(api_key=key)
        result = client.images.generate(
            model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
            prompt=prompt,
            size="1024x1024",
        )
        image_data = result.data[0].b64_json
        if not image_data:
            return jsonify({"error": "No image was returned."}), 502
        return jsonify({"image": "data:image/png;base64," + image_data})
    except Exception:
        app.logger.exception("NUH AI image generation failed")
        return jsonify({"error": "Image generation failed. Check API access and billing."}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
