import streamlit as st
import requests
import time
import datetime
import os
from PIL import Image
from utils.feedback import (
    show_feedback_form,
    get_git_commit_hash,
    submit_feedback_to_mongodb,
)
from dotenv import load_dotenv
from typing import Callable, Any


def measure_response_time(func: Callable[..., Any]) -> Callable[..., tuple[Any, float]]:
    def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # In milliseconds
        return result, response_time

    return wrapper


def translate_chat_history_to_api(
    chat_history: list[dict[str, str]], max_pairs: int = 4
):
    api_format: list[dict[str, str]] = []
    relevant_history = [
        msg for msg in chat_history[1:] if msg["role"] in ["user", "ai"]
    ]

    i = len(relevant_history) - 1
    while i > 0 and len(api_format) < max_pairs:
        ai_msg = relevant_history[i]
        user_msg = relevant_history[i - 1]
        if ai_msg["role"] == "ai" and user_msg["role"] == "user":
            api_format.insert(0, {"User": user_msg["content"], "AI": ai_msg["content"]})
            i -= 2
        else:
            i -= 1
    return api_format


def display_sources_context(context_sources: list[dict[str, str]]):
    with st.expander("Sources and Context"):
        try:
            if context_sources:
                for idx, cs in enumerate(context_sources, 1):
                    st.markdown(f"**Source {idx}**:")
                    if cs.get("source"):
                        st.markdown(f"[{cs['source']}]({cs['source']})")
                    if cs.get("context"):
                        st.markdown(f"**Related Context:**\n> {cs['context']}")
                    st.markdown("---")  # Separator between source-context pairs
            else:
                st.markdown("No Sources or Context Available.")
        except (ValueError, SyntaxError) as e:
            st.markdown(f"Failed to parse sources: {e}")


@measure_response_time
def response_generator(user_input: str) -> tuple[str, str] | tuple[None, None]:
    """
    Use the chat endpoint to generate a response to the user's query.

    Args:
    - user_input (str): The query entered by the user.

    Returns:
    - tuple: Contains the AI response and sources.
    """
    url = f"{st.session_state.base_url}{st.session_state.selected_endpoint}"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    chat_history = translate_chat_history_to_api(st.session_state.chat_history)
    payload = {
        "query": user_input,
        "list_sources": True,
        "list_context": True,
        "chat_history": chat_history,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            st.error("Invalid response format")
            return None, None
        context_sources = data.get("context_sources", [])
        st.session_state.metadata[user_input] = {
            "context_sources": context_sources,
        }
        return data.get("response", ""), context_sources
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return None, None


def main():
    load_dotenv()
    img = Image.open("assets/or_logo.png")
    st.set_page_config(page_title="OR Assistant", page_icon=img)

    deployment_time = datetime.datetime.now(datetime.timezone.utc)
    st.info(f"Deployment time: {deployment_time.strftime('%m/%d/%Y %H:%M')} UTC")

    st.title("OR Assistant")

    base_url = os.getenv("CHAT_ENDPOINT", "http://localhost:8000")
    selected_endpoint = "/conversations/agent-retriever"

    if "selected_endpoint" not in st.session_state:
        st.session_state.selected_endpoint = selected_endpoint

    if "base_url" not in st.session_state:
        st.session_state.base_url = base_url

    if not os.getenv("CHAT_ENDPOINT"):
        st.warning(
            "The CHAT_ENDPOINT environment variable is not set or is empty. DEFAULT: http://localhost:8000"
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "metadata" not in st.session_state:
        st.session_state.metadata = {}

    if not st.session_state.chat_history:
        st.session_state.chat_history.append(
            {
                "content": "Hi, I am the OpenROAD assistant. Type your query about OpenROAD",
                "role": "ai",
            }
        )

    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        if message["role"] == "ai" and idx > 0:
            user_message = st.session_state.chat_history[idx - 1]
            if user_message["role"] == "user":
                user_input = user_message["content"]
                context_sources = st.session_state.metadata.get(user_input, {}).get(
                    "context_sources", []
                )
                display_sources_context(context_sources)

    user_input = st.chat_input("Enter your queries ...")

    if user_input:
        st.session_state.chat_history.append({"content": user_input, "role": "user"})

        with st.chat_message("user"):
            st.markdown(user_input)

        response_tuple, response_time = response_generator(user_input)

        # Validate the response tuple
        if (
            response_tuple
            and isinstance(response_tuple, tuple)
            and len(response_tuple) == 2
        ):
            response, context_sources = response_tuple
            if response is not None:
                response_buffer = response

                with st.chat_message("ai"):
                    message_placeholder = st.empty()
                    message_placeholder.markdown(response_buffer)

                # Display response time
                response_time_text = (
                    f"Response Time: {response_time / 1000:.2f} seconds"
                )
                if response_time < 5000:
                    color = "green"
                elif response_time < 10000:
                    color = "orange"
                else:
                    color = "red"
                st.markdown(f":{color}[{response_time_text}]")

                st.session_state.chat_history.append(
                    {
                        "content": response_buffer,
                        "role": "ai",
                    }
                )
                display_sources_context(context_sources)

            else:
                st.error("Invalid response from the API")

    # Reaction buttons and feedback form
    question_dict = {
        interaction["content"]: i
        for i, interaction in enumerate(st.session_state.chat_history)
        if interaction["role"] == "user"
    }

    # Show feedback buttons if there is at least one question/answer pair
    if question_dict:
        if "feedback_button" not in st.session_state:
            st.session_state.feedback_button = False

        def update_state():
            """
            Update the state of the feedback button.
            """
            st.session_state.feedback_button = True

        # Display reaction buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            thumbs_up = st.button("👍", key="thumbs_up")
        with col2:
            thumbs_down = st.button("👎", key="thumbs_down")
        with col3:
            feedback_clicked = st.button("Feedback", on_click=update_state)

        # Handle thumbs up and thumbs down reactions
        if thumbs_up or thumbs_down:
            try:
                selected_question = st.session_state.chat_history[-2][
                    "content"
                ]  # Last user question
                gen_ans = st.session_state.chat_history[-1][
                    "content"
                ]  # Last AI response
                metadata = st.session_state.metadata.get(selected_question, {})
                context_sources = metadata.get("context_sources", [])

                reaction = "upvote" if thumbs_up else "downvote"

                submit_feedback_to_mongodb(
                    question=selected_question,
                    answer=gen_ans,
                    context_sources=context_sources,
                    issue=reaction,
                    version=get_git_commit_hash(),
                )
                st.success("Thank you for your feedback!")
            except Exception as e:
                st.error(f"Failed to submit feedback: {e}")

        # Feedback form logic
        if feedback_clicked or st.session_state.feedback_button:
            try:
                show_feedback_form(
                    question_dict,
                    st.session_state.metadata,
                    st.session_state.chat_history,
                )
            except Exception as e:
                st.error(f"Failed to load feedback form: {e}")


if __name__ == "__main__":
    main()
