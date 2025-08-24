from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

api_key = os.environ['OPEN_ROUTER']
base_url = os.environ['OPEN_ROUTER_BASE']
MODEL = os.environ['OCR_MODEL']

if not api_key:
    raise ValueError("Please set OPENROUTER_API_KEY in your .env file.")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
   )