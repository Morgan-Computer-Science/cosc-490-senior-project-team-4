from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    agent_type = data.get("agentType", "")

    return jsonify({
        "reply": f"Message received: {message} | Agent: {agent_type}"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)