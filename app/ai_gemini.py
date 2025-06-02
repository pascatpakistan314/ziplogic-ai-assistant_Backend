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




# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-bison-001:generateText"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# GEMINI_API_KEY = "AIzaSyCY4d_sqrw8mQwpvg7eQ4g2_tmnUYN1Ias"
# GEMINI_API_KEY = "AIzaSyCB_m_f_1UT1rT9WhfqaRFiWrOn-gNIhog"
GEMINI_API_KEY = "AIzaSyDqkaqimjZLOy0Z7pJFOCe1VDkiIkWL198"
def call_gemini_api(prompt, max_retries=3, initial_timeout=10):
    """
    Calls the Gemini API with:
    - Retry mechanism (exponential backoff)
    - Better error handling
    - Response validation
    - Timeout management
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    last_error = None

    for attempt in range(max_retries):
        timeout = initial_timeout * (attempt + 1)  # Progressive timeout
        retry_delay = 2 ** attempt  # Exponential backoff (1s, 2s, 4s...)

        try:
            # Make the API request
            response = requests.post(
                GEMINI_API_URL,
                headers=headers,
                params={"key": GEMINI_API_KEY},
                json=payload,
                timeout=timeout
            )

            # Check for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Parse JSON response
            response_data = response.json()

            # Validate response structure
            if not response_data.get('candidates'):
                raise ValueError("Invalid response: Missing 'candidates' field")

            # Success - return the data
            return response_data

        except requests.exceptions.Timeout as e:
            last_error = f"Timeout (attempt {attempt + 1}): {str(e)}"
            logging.warning(last_error)
            if attempt < max_retries - 1:
                sleep(retry_delay)
            continue

        except requests.exceptions.RequestException as e:
            last_error = f"Request error (attempt {attempt + 1}): {str(e)}"
            logging.error(last_error)
            if attempt < max_retries - 1:
                sleep(retry_delay)
            continue

        except ValueError as e:
            last_error = f"Invalid response (attempt {attempt + 1}): {str(e)}"
            logging.error(last_error)
            if attempt < max_retries - 1:
                sleep(retry_delay)
            continue

    # If all retries failed
    raise Exception(f"API call failed after {max_retries} attempts. Last error: {last_error}")