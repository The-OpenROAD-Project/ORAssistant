import requests
import time
import sys
import traceback
from script_based_evaluation.utils.logging_utils import log_error
from script_based_evaluation.models.gpt_model import base_gpt_4o
from script_based_evaluation.models.gemini_model import (
    base_gemini_1_5_flash,
    base_gemini_1_5_pro,
)
from openai import OpenAI


def send_request(
    endpoint: str, query: str, agent_retriever_urls: dict[str, str], client: OpenAI
) -> tuple[str | None, float]:
    try:
        print("Sending request to endpoint:", endpoint)
        if endpoint in agent_retriever_urls:
            url = f"{agent_retriever_urls[endpoint]}/graphs/agent-retriever"
        elif endpoint == "base-gemini-1.5-flash":
            response_text, response_time = base_gemini_1_5_flash(query)
            print("Response:", response_text)
            return response_text, response_time
        elif endpoint == "base-gpt-4o":
            response_text, response_time = base_gpt_4o(query, client)
            print("Response:", response_text)
            return response_text, response_time

        payload = {"query": query, "list_context": True, "list_sources": True}
        print(f"POST {url} with payload: {payload}")
        response = requests.post(url, json=payload)

        try:
            response_json = response.json()
            print("Response:", response_json.get("response"))
            return response_json.get(
                "response"
            ), response.elapsed.total_seconds() * 1000
        except ValueError as e:
            print(f"Error parsing JSON response: {str(e)}")
            return None, response.elapsed.total_seconds() * 1000
    except Exception as e:
        error_message = f"Error in send_request: {str(e)}"
        log_error(error_message, traceback.format_exc())
        raise


def llm_judge(prompt: str) -> str:
    while True:
        try:
            response_text, _ = base_gemini_1_5_pro(prompt)
            return response_text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 10 seconds")
                time.sleep(10)
            else:
                log_error(f"Error in llm_judge: {str(e)}", traceback.format_exc())
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)


def send_request_gemini(prompt: str) -> str:
    while True:
        try:
            response_text, _ = base_gemini_1_5_flash(prompt)
            return response_text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Rate limit exceeded, sleeping for 10 seconds")
                time.sleep(10)
            else:
                log_error(
                    f"Error in send_request_gemini: {str(e)}", traceback.format_exc()
                )
                print(
                    "An error occurred while sending request to Gemini. Check error_log.txt for details."
                )
                sys.exit(1)
