from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()

from agent import app as agent_app

flask_app = Flask(__name__, static_folder="static")
CORS(flask_app)

agent_app.set_up()

@flask_app.route("/")
def index():
    return send_from_directory(flask_app.static_folder, "index.html")

@flask_app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(flask_app.static_folder, filename)

@flask_app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    user_id = data.get("userId", "test-user")

    try:
        result = agent_app.query(message=message, user_id=user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    flask_app.run(debug=True, port=5001)