import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from typing import Optional, Any


import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) 
from common.mongoClient import submit_feedback

load_dotenv()


def get_sheet_title_by_gid(
    spreadsheet_metadata: dict[str, Any], gid: int
) -> Optional[str]:
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
            return str(sheet["properties"]["title"])
    return None


def format_sources(sources: list[str]) -> str:
    """
    Format the sources into a string suitable for Google Sheets.

    Args:
    - sources (list[str]): List of source URLs.

    Returns:
    - str: Formatted sources string.
    """
    assert isinstance(sources, list), "Sources should be a list of strings."
    return "\n".join(sources)


def format_context(context: list[str]) -> str:
    """
    Format the context into a string suitable for Google Sheets.

    Args:
    - context (list[str]): List of context strings.

    Returns:
    - str: Formatted context string.
    """
    assert isinstance(context, list), "Context should be a list of strings."
    return "\n".join(context)


def submit_feedback_to_mongoDB(
    question: str,
    answer: str,
    context_sources: list[dict[str, str]],
    issue: str,
    version: str,
) -> None:
    """
    Submit feedback to a specific MongoDB database.

    Args:
    - question (str): The question for which feedback is being submitted.
    - answer (str): The generated answer to the question.
    - context_sources (list[dict[str, str]]): List of source-context pairs.
    - issue (str): Details about the issue.
    - version (str): Version information.

    Returns:
    - None
    """
    try:
        result = submit_feedback(
            question=question,
            answer=answer,
            context_sources=context_sources,
            issue=issue,
            version=version,
        )
        if not result:
            st.sidebar.error("Failed to submit feedback to MongoDB")
    except Exception as e:
        st.sidebar.error(f"Error submitting feedback to MongoDB: {e}")


def submit_feedback_to_google_sheet(
    question: str,
    answer: str,
    context_sources: list[dict[str, str]],
    issue: str,
    version: str,
    reaction: Optional[str] = None, # Added optional reaction parameter
) -> None:
    """
    Submit feedback to a specific Google Sheet.

    Args:
    - question (str): The question for which feedback is being submitted.
    - answer (str): The generated answer to the question.
    - context_sources (list[dict[str, str]]): List of source-context pairs.
    - issue (str): Details about the issue.
    - version (str): Version information.
    - reaction (Optional[str]): User's reaction ('upvote' or 'downvote').

    Returns:
    - None
    """
    if not os.getenv("GOOGLE_CREDENTIALS_JSON"):
        raise ValueError(
            "The GOOGLE_CREDENTIALS_JSON environment variable is not set or is empty."
        )

    if not os.getenv("FEEDBACK_SHEET_ID"):
        raise ValueError(
            "The FEEDBACK_SHEET_ID environment variable is not set or is empty."
        )

    service_account_file = os.getenv("GOOGLE_CREDENTIALS_JSON")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(service_account_file, scopes=scope)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("FEEDBACK_SHEET_ID", "")
    target_gid = int(os.getenv("FEEDBACK_SHEET_GID", "0"))

    spreadsheet = client.open_by_key(sheet_id)
    sheet_metadata = spreadsheet.fetch_sheet_metadata()
    sheet_metadata_dict = dict(sheet_metadata)

    sheet_title = get_sheet_title_by_gid(sheet_metadata_dict, target_gid)
    if sheet_title:
        sheet = spreadsheet.worksheet(sheet_title)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Format sources and context as combined pairs
        formatted_pairs = []
        for cs in context_sources:
            source = cs.get('source', '')
            context = cs.get('context', '')
            if source or context:
                formatted_pairs.append(f"Source: {source}\nContext: {context}")
        
        formatted_content = "\n\n".join(formatted_pairs)

        data_to_append = [
            question,
            answer,
            formatted_content,  # Combined source-context pairs
            issue,
            timestamp,
            version,
            reaction or "",
        ]

        #
        headers = sheet.row_values(1)
        required_headers = [
            "Question",
            "Answer",
            "Source-Context Pairs",  # Updated header
            "Issue",
            "Timestamp",
            "Version",
            "Reaction",
        ]

        if headers != required_headers:
            sheet.clear()
            sheet.append_row(required_headers)
            sheet.format("A1:G1", {"textFormat": {"bold": True}})

        sheet.append_row(data_to_append)
    else:
        st.sidebar.error(f"Sheet with GID {target_gid} not found.")


def show_feedback_form(
    questions: dict[str, int],
    metadata: dict[str, dict[str, str]],
    interactions: list[dict[str, str]],
) -> None:
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
        context_sources = metadata[selected_question].get("context_sources", [])

        if st.sidebar.button("Submit"):
            selected_index = questions[selected_question]
            gen_ans = interactions[selected_index + 1]["content"]

            submit_feedback_to_google_sheet(
                question=selected_question,
                answer=gen_ans,
                context_sources=context_sources,
                issue=feedback,
                version=os.getenv("RAG_VERSION", get_git_commit_hash()),
            )
            submit_feedback_to_mongoDB(
                question=selected_question,
                answer=gen_ans,
                context_sources=context_sources,
                issue=feedback,
                version=os.getenv("RAG_VERSION", get_git_commit_hash()),
            )

            st.session_state.submitted = True

    if st.session_state.submitted:
        st.sidebar.success("Thank you for your feedback!")


def get_git_commit_hash() -> str:
    """
    Get the latest commit hash from the Git repository.

    Returns:
    - str: The latest commit hash.
    """
    import subprocess

    try:
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        commit_hash = "N/A"

    return commit_hash
