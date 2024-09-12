# app.py
from flask import Flask, request, jsonify
import agent

app = Flask(__name__)


@app.route("/run_agent", methods=["POST"])
def _run_agent():
    data = request.json
    result = agent.run_agent(data["system_prompt"], data["transcript"])
    return jsonify(result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
