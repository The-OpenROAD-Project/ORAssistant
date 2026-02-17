import os
import time
import sys
import traceback
from google import genai
from google.genai import types
from script_based_evaluation.utils.logging_utils import log_error

_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_safety_config = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]


def base_gemini_1_5_flash(query: str) -> tuple[str, float]:
    while True:
        try:
            start_time = time.time()
            response = _client.models.generate_content(
                model="gemini-2.0-flash",
                contents=" " + query,
                config=types.GenerateContentConfig(
                    safety_settings=_safety_config,
                ),
            )
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response.text or "", response_time
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 60 seconds")
                time.sleep(60)
            else:
                log_error(
                    f"Error in base_gemini_1_5_flash: {str(e)}", traceback.format_exc()
                )
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)


def base_gemini_1_5_pro(query: str) -> tuple[str, float]:
    while True:
        try:
            start_time = time.time()
            response = _client.models.generate_content(
                model="gemini-2.5-pro",
                contents=" " + query,
                config=types.GenerateContentConfig(
                    safety_settings=_safety_config,
                    max_output_tokens=2000,
                    temperature=0.0,
                ),
            )
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response.text or "", response_time
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 60 seconds")
                time.sleep(60)
            else:
                log_error(
                    f"Error in base_gemini_1_5_pro: {str(e)}", traceback.format_exc()
                )
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)
