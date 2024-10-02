# client.py
import requests

from datetime import datetime

# Get the current date and time
date_time = datetime.now().strftime("%Y-%m-%d %H:%M")



transcript = [
    "Hello, thank you for calling our health center. Can you verify your name? ",
]

url = "http://localhost:5001/run_agent"


def get_user_input():
    return input("User: ")


def get_ai_response(transcript):
    response = requests.post(
        url, json={"phone_number": '215-932-4488', "transcript": transcript}
    )
    return response.json()["result"]


print("AI: " + transcript[-1])

while True:
    user_input = get_user_input()
    transcript.append(user_input)

    ai_response = get_ai_response(transcript)
    transcript.append(ai_response)

    print("AI: " + ai_response)

    if "goodbye" in user_input.lower() or "bye" in user_input.lower():
        print("Call ended. Thank you for using our service!")
        break
