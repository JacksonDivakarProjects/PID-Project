from dotenv import load_dotenv
import os
# from openai import OpenAI
from groq import Groq

from inference_sdk import InferenceHTTPClient

load_dotenv()

api_key = os.environ['OPEN_ROUTER']
base_url = os.environ['OPEN_ROUTER_BASE']
MODEL = os.environ['OCR_MODEL']

if not api_key:
    raise ValueError("Please set OPENROUTER_API_KEY in your .env file.")

client = Groq(api_key="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")

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key='ezRD6iXIbVeZMHDl6T28'
)

# Mapping dictionary
CLASS_MAPPING = {
    '1': 'Gate Valve', '2': 'Globe Valve', '3': 'Ball Valve', '4': 'Check Valve', '5': 'Pressure Instrument',
    '6': 'Control Valve', '7': 'Tagged Gate Valve', '8': 'Local Control Station', '9': 'Butterfly Valve',
    '10': 'Equipment Tag', '11': 'Diaphragm Valve', '12': 'Plug Valve', '13': 'Needle Valve',
    '14': 'Solenoid Valve', '15': 'Actuated Gate Valve', '16': 'Manual Butterfly Valve',
    '17': 'Safety Relief Valve', '18': 'Process Line Valve', '19': 'Level Instrument',
    '20': 'Flow Instrument', '21': 'Inline Strainer', '22': 'Speciality Valve',
    '23': 'Junction Box ID', '24': 'System Interface', '25': 'Tagged Control Valve',
    '26': 'Temperature Instrument', '27': 'High-Pressure Valve',
    '28': 'Utility Line Valve', '29': 'Drain Valve', '30': 'Operator Station',
    '31': 'Tagged Ball Valve', '32': 'Analysis Instrument'
}