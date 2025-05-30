# import google.generativeai as genai
# import os
#
# def call_gemini_api(prompt):
#     genai.configure(api_key="AIzaSyCY4d_sqrw8mQwpvg7eQ4g2_tmnUYN1Ias")
#     model = genai.GenerativeModel("models/gemini-2.0-flash")
#
#     response = model.generate_content(prompt)
#
#     # Return just the string text (not the full object)
#     return response.candidates[0].content.parts[0].text


from datetime import datetime
import os
import shutil
import uuid
import json
import requests
import re
import logging
from time import sleep
from json.decoder import JSONDecodeError




GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-bison-001:generateText"

GEMINI_API_KEY = "AIzaSyCY4d_sqrw8mQwpvg7eQ4g2_tmnUYN1Ias"
def call_gemini_api(prompt, max_retries=3, initial_timeout=30):
    """
    Enhanced API caller with retry logic and better error handling
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    for attempt in range(max_retries):
        timeout = initial_timeout * (attempt + 1)  # Exponential backoff
        try:
            response = requests.post(
                GEMINI_API_URL,
                headers=headers,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            # Validate response structure
            response_data = response.json()
            if not response_data.get('candidates'):
                raise ValueError("Invalid response structure: missing candidates")

            return response_data

        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise Exception(f"API timeout after {max_retries} attempts")
            sleep(2 ** attempt)  # Exponential backoff

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"API request failed: {str(e)}")
            sleep(1)  # Short delay before retry
