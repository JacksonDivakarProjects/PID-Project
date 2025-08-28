from dotenv import load_dotenv
import os
# from openai import OpenAI
from groq import Groq

load_dotenv()

api_key = os.environ['OPEN_ROUTER']
base_url = os.environ['OPEN_ROUTER_BASE']
MODEL = os.environ['OCR_MODEL']

if not api_key:
    raise ValueError("Please set OPENROUTER_API_KEY in your .env file.")

client = Groq(api_key="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")