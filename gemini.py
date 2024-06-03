import pathlib
import textwrap

import google.generativeai as genai

import os
from dotenv import load_dotenv

load_dotenv()

# Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY', None)

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("What is the meaning of life?")

print(response.text)