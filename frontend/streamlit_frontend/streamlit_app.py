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
from typing import Callable, Any


def measure_response_time(func: Callable[..., Any]) -> Callable[..., tuple[Any, float]]:
    def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # In milliseconds
        return result, response_time

    return wrapper


def translate_chat_history_to_api(chat_history: list[dict[str, str]], max_pairs: int = 4) -> list[dict[str, str]]:
    """
    Translate the chat history to the format expected by the API.

    Args:
    - chat_history (list): The chat history.
    - max_pairs (int): The maximum number of chat pairs to include in the API request.

    Returns:
    - list: The chat history formatted for the API.
    """
    api_format: list[dict[str, str]] = []
    # Skip the first AI message (starter message) and get the last messages
    relevant_history = [msg for msg in chat_history[1:] if msg['role'] in ['user', 'ai']]
    
    # Process messages in reverse order to get the most recent pairs
    user_msg = None
    for msg in reversed(relevant_history):
        if msg['role'] == 'user' and user_msg is None:
            user_msg = msg
        elif msg['role'] == 'ai' and user_msg is not None:
            api_format.insert(0, {
                "User": user_msg['content'],
                "AI": msg['content']
            })
            user_msg = None
            if len(api_format) == max_pairs:
                break
    
    return api_format

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

    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}

    chat_history = translate_chat_history_to_api(st.session_state.chat_history)
    
    payload = {
        'query': user_input,
        'list_sources': True,
        'list_context': True,
        'chat_history': chat_history
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        try:
            data = response.json()
            if not isinstance(data, dict):
                st.error('Invalid response format')
                return None, None
        except ValueError:
            st.error('Failed to decode JSON response')
            return None, None

        sources = data.get('sources', '')
        st.session_state.metadata[user_input] = {
            'sources': sources,
            'context': data.get('context', ''),
        }

        return data.get('response', ''), sources

    except requests.exceptions.RequestException as e:
        st.error(f'Request failed: {e}')
        return None, None


def main() -> None:
    load_dotenv()

    img = Image.open('assets/or_logo.png')
    st.set_page_config(page_title='OR Assistant', page_icon=img)

    deployment_time = datetime.datetime.now(pytz.timezone('UTC'))
    st.info(f'Deployment time: {deployment_time.strftime("%m/%d/%Y %H:%M")} UTC')

    st.title('OR Assistant')

    base_url = os.getenv('CHAT_ENDPOINT', 'http://localhost:8000')
    selected_endpoint = '/graphs/agent-retriever'  # Hardcoded endpoint

    if 'selected_endpoint' not in st.session_state:
        st.session_state.selected_endpoint = selected_endpoint

    if 'base_url' not in st.session_state:
        st.session_state.base_url = base_url

    if not os.getenv('CHAT_ENDPOINT'):
        st.warning(
            'The CHAT_ENDPOINT environment variable is not set or is empty. DEFAULT: http://localhost:8000'
        )

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'metadata' not in st.session_state:
        st.session_state.metadata = {}
    if 'sources' not in st.session_state:
        st.session_state.sources = {}

    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            'content': 'Hi, I am the OpenROAD assistant. Type your query about OpenROAD',
            'role': 'ai',
        })

    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

        if message['role'] == 'user' and message['content'] in st.session_state.sources:
            with st.expander('Sources:'):
                sources = st.session_state.sources[message['content']]
                try:
                    if isinstance(sources, str):
                        cleaned_sources = sources.replace('{', '[').replace('}', ']')
                        parsed_sources = ast.literal_eval(cleaned_sources)
                    else:
                        parsed_sources = sources
                    if isinstance(parsed_sources, (list, set)):
                        sources_list = '\n'.join(
                            f"- [{link}]({link})"
                            for link in parsed_sources
                            if link.strip()
                        )
                        st.markdown(sources_list)
                    else:
                        st.markdown('No valid sources found.')
                except (ValueError, SyntaxError) as e:
                    st.markdown(f'Failed to parse sources: {e}')

    user_input = st.chat_input('Enter your queries ...')

    if user_input:
        st.session_state.chat_history.append({'content': user_input, 'role': 'user'})

        with st.chat_message('user'):
            st.markdown(user_input)

        response_tuple, response_time = response_generator(user_input)

        # Validate the response tuple
        if (
            response_tuple
            and isinstance(response_tuple, tuple)
            and len(response_tuple) == 2
        ):
            response, sources = response_tuple
            if response is not None:
                response_buffer = response  # Include the AI response in the response buffer

                with st.chat_message('ai'):
                    message_placeholder = st.empty()

                    # Option 1: Streaming effect - Send response in chunks
                    for chunk in response.split(' '):
                        response_buffer += chunk + ' '
                        message_placeholder.markdown(response_buffer)  # Update message with current buffer
                        time.sleep(0.05)  # Delay for streaming effect

                    # Final update to ensure complete response is shown
                    message_placeholder.markdown(response_buffer)

                response_time_text = (
                    f'Response Time: {response_time / 1000:.2f} seconds'
                )
                response_time_colored = f":{'green' if response_time < 5000 else 'orange' if response_time < 10000 else 'red'}[{response_time_text}]"
                st.markdown(response_time_colored)
                st.session_state.chat_history.append({
                    'content': response_buffer,
                    'role': 'ai',
                })

                st.session_state.sources[user_input] = sources

                if sources:
                    with st.expander('Sources:'):
                        try:
                            if isinstance(sources, str):
                                cleaned_sources = sources.replace('{', '[').replace(
                                    '}', ']'
                                )
                                parsed_sources = ast.literal_eval(cleaned_sources)
                            else:
                                parsed_sources = sources
                            if isinstance(parsed_sources, (list, set)):
                                sources_list = '\n'.join(
                                    f'- [{link}]({link})'
                                    for link in parsed_sources
                                    if link.strip()
                                )
                                st.markdown(sources_list)
                            else:
                                st.markdown('No valid sources found.')
                        except (ValueError, SyntaxError) as e:
                            st.markdown(f'Failed to parse sources: {e}')
        else:
            st.error('Invalid response from the API')

    question_dict = {
        interaction['content']: i
        for i, interaction in enumerate(st.session_state.chat_history)
        if interaction['role'] == 'user'
    }
    if question_dict and os.getenv('FEEDBACK_SHEET_ID'):
        if 'feedback_button' not in st.session_state:
            st.session_state.feedback_button = False

        def update_state() -> None:
            """
            Update the state of the feedback button.
            """
            st.session_state.feedback_button = True

        if (
            st.button('Feedback', on_click=update_state)
            or st.session_state.feedback_button
        ):
            try:
                show_feedback_form(
                    question_dict,
                    st.session_state.metadata,
                    st.session_state.chat_history,
                )
            except Exception as e:
                st.error(f'Failed to load feedback form: {e}')


if __name__ == '__main__':
    main()