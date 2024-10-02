# app.py
from flask import Flask, request, jsonify
import agent
import logging
from pyngrok import ngrok
import os
import argparse

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# start ngrok
ngrok_auth_token = os.getenv('NGROK_TOKEN')


def start_ngrok(start_ngrok):
    if start_ngrok:
        try:
            ngrok.set_auth_token(ngrok_auth_token)
            ngrok_http = ngrok.connect(
                5001, domain="probable-instantly-crab.ngrok-free.app"
            )
            public_url = ngrok_http.public_url
            print(f"ngrok tunnel established: {public_url}")
            return public_url
        except Exception as e:
            logging.error(f"Error starting ngrok: {e}")
            return None
    else:
        return "http://localhost:5001"  # Use localhost if ngrok is not started


@app.route("/", methods=["GET"])
def health_check():
    return jsonify(status="App is running"), 200


@app.route("/run_agent", methods=["POST"])
def _run_agent():
    data = request.json
    logging.info(f"Received request body: {data}")
    result = agent.run_agent(
        data["transcript"], data["phone_number"])
    return jsonify(result=result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_ngrok', action='store_true',
                        help='Start ngrok tunnel')
    args = parser.parse_args()

    public_url = start_ngrok(args.start_ngrok)

    if public_url is None:
        logging.error("Failed to start ngrok. Exiting.")
        exit(1)

    logging.info(f"App is running. Public URL: {public_url}")
    app.run(host="0.0.0.0", port=5001)
