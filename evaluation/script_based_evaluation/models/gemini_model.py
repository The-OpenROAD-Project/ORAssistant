import time
import sys
import traceback
import vertexai.preview.generative_models as genai
from vertexai.generative_models import (
    HarmCategory,
    HarmBlockThreshold,
    SafetySetting,
)
from script_based_evaluation.utils.logging_utils import log_error


def base_gemini_1_5_flash(query: str) -> tuple[str, float]:
    safety_config = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    while True:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            start_time = time.time()
            query = " " + query
            response = model.generate_content(query, safety_settings=safety_config)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            return response.text, response_time
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 10 seconds")
                time.sleep(10)
            else:
                error_message = f"Error in base_gemini_1_5_flash: {str(e)}"
                error_details = traceback.format_exc()
                log_error(error_message, error_details)
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)


def base_gemini_1_5_pro(query: str) -> tuple[str, float]:
    safety_config = [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    while True:
        try:
            model = genai.GenerativeModel("gemini-2.5-pro")
            start_time = time.time()
            query = " " + query
            response = model.generate_content(
                query,
                safety_settings=safety_config,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.0,
                ),
            )
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            return response.text, response_time
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 10 seconds")
                time.sleep(10)
            else:
                error_message = f"Error in base_gemini_1_5_flash: {str(e)}"
                error_details = traceback.format_exc()
                log_error(error_message, error_details)
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)
