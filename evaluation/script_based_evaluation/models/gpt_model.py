import time
import sys
import traceback
from openai import OpenAI
from script_based_evaluation.utils.logging_utils import log_error


def base_gpt_4o(query: str, client: OpenAI) -> tuple[str, float]:
    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": query}]
        )
        response_content = completion.choices[0].message.content
        if response_content is not None:
            response = response_content.strip()
        else:
            response = ""
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return response, response_time
    except Exception as e:
        error_message = f"Error in base_gpt_4o: {str(e)}"
        error_details = traceback.format_exc()
        log_error(error_message, error_details)
        sys.exit(1)
