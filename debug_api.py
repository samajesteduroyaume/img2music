import os
from dotenv import load_dotenv
import google.generativeai as genai

# Charge .env
load_dotenv()

key = os.getenv("GEMINI_API_KEY")

print(f"Current Working Report: {os.getcwd()}")
print(f"Key loaded: {key is not None}")
if key:
    print(f"Key length: {len(key)}")
    print(f"Key start: {key[:5]}...")
    
    # Test simple API call
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Hello")
        print("API Call Success!")
    except Exception as e:
        print(f"API Call Failed: {e}")
else:
    print("Environment variable GEMINI_API_KEY is not set.")
    # Check if file exists
    if os.path.exists(".env"):
        print(".env file found.")
        with open(".env", "r") as f:
            print("Content preview:")
            print(f.read())
    else:
        print(".env file NOT found in current directory.")
