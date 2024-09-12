# client.py
import requests

system_prompt = "you are a call center representative."
transcript = [
    "hello, how can i help you?",
    "I am calling to reschedule my appointment.",
]

url = "http://localhost:5001/run_agent"
response = requests.post(
    url, json={"system_prompt": system_prompt, "transcript": transcript}
)

result = response.json()["result"]
print(f"Result: {result}")
