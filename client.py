# client.py
import requests

from datetime import datetime

# Get the current date and time
date_time = datetime.now().strftime("%Y-%m-%d %H:%M")


system_message = f"""
                You are a call center agent at Signify Health. You have received a call from a call from a member. \
                The members usually call regarding their appointments, may have questions, or they need to update their information.  \
                The member's phone number is 555-546-6270. The current date and time is {date_time}
                """


transcript = [
    "Hello, thank you for calling our health center. Can you verify your name? ",
]

url = "http://localhost:5001/run_agent"


def get_user_input():
    return input("User: ")


def get_ai_response(transcript):
    response = requests.post(
        url, json={"system_message": system_message, "transcript": transcript}
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
