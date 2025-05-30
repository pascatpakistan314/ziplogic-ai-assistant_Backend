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

OPENAI_API_KEY ="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"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def call_openai_api(prompt, model="gpt-3.5-turbo", temperature=0.0, max_tokens=1500):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=data, timeout=60)
    if response.status_code != 200:
        try:
            error_info = response.json()
        except json.JSONDecodeError:
            error_info = response.text
        raise Exception(f"OpenAI API error {response.status_code}: {error_info}")

    res_json = response.json()
    raw_content = res_json['choices'][0]['message']['content']

    # Clean markdown backticks if any
    cleaned = re.sub(r"```(?:json)?\n?|```", "", raw_content).strip()

    # Extract JSON object substring
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start >= 0 and end > start:
        cleaned = cleaned[start:end]

    return cleaned