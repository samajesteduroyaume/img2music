import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    models = genai.list_models()
    for model in models:
        print(f"Model: {model.name}, Supported methods: {model.supported_generation_methods}")
else:
    print("API key not configured")