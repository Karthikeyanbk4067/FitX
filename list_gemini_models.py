import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.environ.get('AIzaSyDn3prIvz_HZQ3UQtYYB7qnHnEZ5CR435E')
genai.configure(api_key=api_key)
models = genai.list_models()
for m in models:
    print(m.name)
