import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

def get_sheet_title_by_gid(spreadsheet_metadata: dict, gid: int) -> Optional[str]:
    """
    Get the sheet title by Sheet GID

    Args:
    - spreadsheet_metadata (dict): Metadata dictionary of the Google Sheet.
    - gid (int): The Grid ID of the sheet.

    Returns:
    - Optional[str]: The title of the sheet with the given GID or None if not found.
    """
    sheets = spreadsheet_metadata["sheets"]
    for sheet in sheets:
        if sheet["properties"]["sheetId"] == int(gid):
            return sheet["properties"]["title"]
    return None

def format_sources(sources: list[str]) -> str:
    """
    Format the sources into a string suitable for Google Sheets.

    Args:
    - sources (list[str]): List of source URLs.

    Returns:
    - str: Formatted sources string.
    """
    if isinstance(sources, list):
        return "\n".join(sources)
    return str(sources)

def format_context(context: list[str]) -> str:
    """
    Format the context into a string suitable for Google Sheets.

    Args:
    - context (list[str]): List of context strings.

    Returns:
    - str: Formatted context string.
    """
    if isinstance(context, list):
        return "\n".join(context)
    return str(context)

def submit_feedback_to_google_sheet(
    question: str,
    answer: str,
    sources: str,
    context: str,
    issue: str,
    version: str
) -> None:
    """
    Submit feedback to a specific Google Sheet.

    Args:
    - question (str): The question for which feedback is being submitted.
    - answer (str): The generated answer to the question.
    - sources (str): Source data used for the answer.
    - context (str): Additional context from the RAG.
    - issue (str): Details about the issue.
    - version (str): Version information.

    Returns:
    - None
    """
    if not os.getenv("GOOGLE_CREDENTIALS_JSON"):
        raise ValueError(
            "The GOOGLE_CREDENTIALS_JSON environment variable is not set or is empty."
        )

    if not os.getenv("FEEDBACK_SHEET_ID"):
        raise ValueError("The FEEDBACK_SHEET_ID environment variable is not set or is empty.")

    if not os.getenv("RAG_VERSION"):
        raise ValueError("The RAG_VERSION environment variable is not set or is empty.")

    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_JSON")
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("FEEDBACK_SHEET_ID")
    target_gid = 0
    if os.getenv("FEEDBACK_SHEET_GID"):
        target_gid = os.getenv("FEEDBACK_SHEET_GID")

    spreadsheet = client.open_by_key(sheet_id)
    sheet_metadata = spreadsheet.fetch_sheet_metadata()

    sheet_title = get_sheet_title_by_gid(sheet_metadata, target_gid)
    if sheet_title:
        sheet = spreadsheet.worksheet(sheet_title)
        timestamp = datetime.now(timezone.utc).isoformat()
        formatted_sources = format_sources(sources) 
        formatted_context = format_context(context)  
        data_to_append = [question, answer, formatted_sources, formatted_context, issue, timestamp, version]

        if not sheet.row_values(1):
            sheet.format("A1:G1", {"textFormat": {"bold": True}})
            sheet.append_row(
                [
                    "Question",
                    "Answer",
                    "Sources",
                    "Context",
                    "Issue",
                    "Timestamp",
                    "Version",
                ],
                1,
            )

        sheet.append_row(data_to_append)
        st.sidebar.success("Feedback submitted successfully.")
    else:
        st.sidebar.error(f"Sheet with GID {target_gid} not found.")

def show_feedback_form(questions: dict[str, int], metadata: dict[str, dict[str, str]], interactions: list[dict[str, str]]) -> None:
    """
    Display feedback form in the sidebar.

    Args:
    - questions (dict[str, int]): Dictionary of questions and indices.
    - metadata (dict[str, dict[str, str]]): Metadata contains sources and context for each question.
    - interactions (list[dict[str, str]]): List of chat interactions from st.session_state.chat_history

    Returns:
    - None
    """
    st.sidebar.title("Feedback Form")

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    question_options = list(questions.keys())
    selected_question = st.sidebar.selectbox(
        "Select the question you faced an issue with:", question_options
    )
    feedback = st.sidebar.text_area("Please provide your feedback or report an issue:")

    if selected_question:
        sources = metadata[selected_question].get("sources", "N/A")
        context = metadata[selected_question].get("context", "N/A")

        if st.sidebar.button("Submit"):
            selected_index = questions[selected_question]
            gen_ans = interactions[selected_index + 1]["content"]

            submit_feedback_to_google_sheet(
                question=selected_question,
                answer=gen_ans,
                sources=sources,
                context=context,
                issue=feedback,
                version=os.getenv("RAG_VERSION", "N/A"),
            )

            st.session_state.submitted = True

    if st.session_state.submitted:
        st.sidebar.success("Thank you for your feedback!")