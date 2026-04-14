import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()

from agent import app as agent_app

flask_app = Flask(__name__, static_folder="static")
CORS(flask_app)

agent_app.set_up()

# ── PDF text extraction ───────────────────────────────────────────────────────
def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages  = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n".join(pages).strip()
    except ImportError:
        return "(pypdf not installed — run: pip install pypdf)"
    except Exception as e:
        return f"(Could not extract text from PDF: {e})"


# ── Routes ────────────────────────────────────────────────────────────────────
@flask_app.route("/")
def index():
    return send_from_directory(flask_app.static_folder, "index.html")

@flask_app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(flask_app.static_folder, filename)

@flask_app.route("/api/health")
def health():
    return jsonify({"status": "ready", "agents": ["ADVISING", "LEARNING", "SUPPORT"]})

@flask_app.route("/api/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file      = request.files["file"]
    doc_type  = request.form.get("type", "transcript")   # "transcript" | "resume"

    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"error": "File too large. Maximum size is 5 MB."}), 400

    text = extract_pdf_text(file_bytes)

    if not text or len(text) < 20:
        return jsonify({"error": "Could not read any text from this PDF. Make sure it is not a scanned image."}), 422

    # Truncate so it doesn't overwhelm the context window
    max_chars = 4000 if doc_type == "transcript" else 3000
    truncated = False
    if len(text) > max_chars:
        text      = text[:max_chars]
        truncated = True

    return jsonify({
        "success":   True,
        "filename":  file.filename,
        "type":      doc_type,
        "chars":     len(text),
        "truncated": truncated,
        "text":      text,
    })

@flask_app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json()
    message = data.get("message", "").strip()
    user_id = data.get("userId", "test-user")
    history = data.get("history", [])
    profile = data.get("profile", None)

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        result = agent_app.query(
            message=message,
            user_id=user_id,
            history=history,
            profile=profile,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    flask_app.run(debug=True, port=5001)