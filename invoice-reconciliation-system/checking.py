import os
from dotenv import load_dotenv
from google import genai

# Load key from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

response = client.interactions.create(
    model="gemini-3.6-flash",
    input="Hello! Confirm you are online."
)

print(response.output_text)