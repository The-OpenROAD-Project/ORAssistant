import streamlit as st
import requests
import time
import datetime
import pytz
import os
import ast
from PIL import Image
from utils.feedback import show_feedback_form
from dotenv import load_dotenv

load_dotenv()

img = Image.open("assets/or_logo.png")
st.set_page_config(page_title="OR Assistant", page_icon=img)

deployment_time = datetime.datetime.now(pytz.timezone("UTC"))
st.info(f'Deployment time: {deployment_time.strftime("%m/%d/%Y %H:%M")} UTC')

st.title("OR Assistant")

if not os.getenv("CHAT_ENDPOINT"):
    st.warning(
        "The CHAT_ENDPOINT environment variable is not set or is empty. DEFAULT: http://localhost:8000/chatApp"
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "metadata" not in st.session_state:
    st.session_state.metadata = {}

if not st.session_state.chat_history:
    st.session_state.chat_history.append({
        "content": "Hi, I am the OpenROAD assistant. Type your query about OpenROAD",
        "role": "ai",
    })

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Enter your queries ...")


def response_generator(user_input: str) -> tuple[str, str]:
    """
    Use the chat endpoint to generate a response to the user's query.

    Args:
    - user_input (str): The query entered by the user.

    Returns:
    - tuple: Contains the AI response and sources.
    """
    url = os.getenv("CHAT_ENDPOINT", "http://localhost:8000/chatApp")

    headers = {"accept": "application/json", "Content-Type": "application/json"}

    payload = {"query": user_input, "listSources": True, "listContext": True}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        try:
            data = response.json()
            if not isinstance(data, dict):
                st.error("Invalid response format")
                return

        except ValueError:
            st.error("Failed to decode JSON response")
            return

        sources = data.get("sources", "")
        st.session_state.metadata[user_input] = {
            "sources": sources,
            "context": data.get("context", ""),
        }

        return data.get("response", ""), sources

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return None, None


if user_input:
    st.session_state.chat_history.append({"content": user_input, "role": "user"})

    with st.chat_message("user"):
        st.markdown(user_input)

    response, sources = response_generator(user_input)
    if response is not None:
        response_buffer = ""

        with st.chat_message("ai"):
            message_placeholder = st.empty()

            for word in response.split():
                response_buffer += word + " "
                message_placeholder.markdown(response_buffer)
                time.sleep(0.05)

        st.session_state.chat_history.append({"content": response_buffer, "role": "ai"})

        if sources:
            with st.expander("Sources:"):
                try:
                    print(sources)
                    if isinstance(sources, str):
                        cleaned_sources = sources.replace("{", "[").replace("}", "]")
                        parsed_sources = ast.literal_eval(cleaned_sources)
                        print(parsed_sources)
                    else:
                        parsed_sources = sources
                    if isinstance(parsed_sources, (list, set)):
                        sources_list = "\n".join(
                            f"- [{link}]({link})"
                            for link in parsed_sources
                            if link.strip()
                        )
                        st.markdown(sources_list)
                    else:
                        st.markdown("No valid sources found.")
                except (ValueError, SyntaxError) as e:
                    st.markdown(f"Failed to parse sources: {e}")

question_dict = {
    interaction["content"]: i
    for i, interaction in enumerate(st.session_state.chat_history)
    if interaction["role"] == "user"
}
if question_dict:
    if "feedback_button" not in st.session_state:
        st.session_state.feedback_button = False

    def update_state() -> None:
        """
        Update the state of the feedback button.
        """
        st.session_state.feedback_button = True

    if st.button("Feedback", on_click=update_state) or st.session_state.feedback_button:
        try:
            show_feedback_form(
                question_dict, st.session_state.metadata, st.session_state.chat_history
            )
        except Exception as e:
            st.error(f"Failed to load feedback form: {e}")
