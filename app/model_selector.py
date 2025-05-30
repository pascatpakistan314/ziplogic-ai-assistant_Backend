import logging
from .ai_gemini import call_gemini_api
from .ai_groq import call_groq_api
from .ai_gpt import call_openai_api

logger = logging.getLogger(__name__)

def call_model(prompt, model='gemini'):
    try:
        if model == 'groq':
            return call_groq_api(prompt)
        elif model == 'gpt':
            return call_gpt_api(prompt)
        else:
            return call_gemini_api(prompt)
    except Exception as e:
        logger.warning(f"{model} failed: {str(e)}")
        if model != 'gpt':
            return call_gpt_api(prompt)  # Fallback
        raise
