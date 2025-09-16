# test_gemini.py
import os
import google.generativeai as genai

# --- IMPORTANT ---
# Paste your API key directly here for this test.
# This is ONLY for testing. Do not do this in your main app.
TEST_API_KEY = "AIzaSyCatYtOViLXubbfjVWlvm9jNkg27C05w60"

try:
    print("Attempting to configure Gemini API...")
    genai.configure(api_key=TEST_API_KEY)
    
    print("Configuration successful. Creating model...")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    print("Model created. Generating content...")
    response = model.generate_content("Hello, world.")
    
    print("\n--- SUCCESS! ---")
    print(response.text)
    print("------------------")

except Exception as e:
    print("\n--- TEST FAILED ---")
    print(f"An error occurred: {e}")
    print("-------------------")