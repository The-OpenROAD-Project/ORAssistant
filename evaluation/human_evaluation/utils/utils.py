import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from typing import Any
import os

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_FORM_ID = os.getenv("GOOGLE_FORM_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=creds)
forms_service = build("forms", "v1", credentials=creds)


def parse_custom_input(custom_input: str, max_value: int) -> list[int]:
    """
    Parse custom input for row ranges and return a sorted list of row numbers.

    Args:
    - custom_input (str): A string representing the custom input for row ranges.
    - max_value (int): The maximum row number available.

    Returns:
    - list[int]: A sorted list of row numbers.
    """
    result: list[int] = []
    ranges = custom_input.split(",")
    for r in ranges:
        if "-" in r:
            start, end = r.split("-")
            start = int(start) if start else 2
            end = int(end) if end else max_value + 1
            result.extend(range(start, end + 1))
        else:
            result.append(int(r))
    return sorted(set(result))


def selected_questions(
    questions: list[dict[str, Any]], parsed_values: list[int]
) -> list[dict[str, Any]]:
    """
    Select questions based on parsed values.

    Args:
    - questions (list[dict[str, Any]]): List of questions.
    - parsed_values (list[int]): List of parsed row numbers from the parse_custom_input function.

    Returns:
    - list[dict[str, Any]]: List of selected questions.
    """
    selected_questions: list[dict[str, Any]] = []
    for index in parsed_values:
        zero_based_index = index - 2
        if 0 <= zero_based_index < len(questions):
            selected_questions.append(questions[zero_based_index])
    return selected_questions


def read_question_and_description() -> list[dict[str, str]]:
    """
    Read questions and descriptions from Google Sheets.

    Returns:
    - list[dict[str, str]]: List of dictionaries containing questions and descriptions.
    """
    try:
        sheet = sheets_service.spreadsheets()
        result = (
            sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range="A2:B").execute()
        )
        values = result.get("values", [])

        questions_and_descriptions: list[dict[str, str]] = []
        for row in values:
            question = row[0] if len(row) > 0 else None
            description = row[1] if len(row) > 1 else ""
            if question:
                questions_and_descriptions.append({
                    "question": question,
                    "description": description,
                })
            else:
                pass
        return questions_and_descriptions
    except HttpError as error:
        st.error("Rate Limited! Please try after a few seconds.")
        st.error(f"An error occurred: {error}")
        return []


def update_gform(questions_descriptions: list[dict[str, str]]) -> None:
    """
    Update Google Form with provided questions and descriptions.

    Args:
    - questions_descriptions (list[dict[str, str]]): List of dictionaries containing questions and descriptions.
    """
    try:
        form = forms_service.forms().get(formId=GOOGLE_FORM_ID).execute()
        items = form.get("items", [])

        requests: list[dict[str, Any]] = []
        # Using Gform API to update the form with the new questions and descriptions in radio button format
        for i, qd in enumerate(questions_descriptions):
            if i < len(items):
                item_id = items[i]["itemId"]
                update_request = {
                    "updateItem": {
                        "item": {
                            "itemId": item_id,
                            "title": qd.get("question", ""),
                            "description": qd.get("description", ""),
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",
                                        "options": [
                                            {"value": "Accept"},
                                            {"value": "Reject"},
                                            {"isOther": True},
                                        ],
                                        "shuffle": False,
                                    },
                                }
                            },
                        },
                        "location": {"index": i},
                        "updateMask": "*",
                    },
                }
                requests.append(update_request)
            else: #If update is not required, create a new question and description
                create_request = {
                    "createItem": {
                        "item": {
                            "title": qd.get("question", ""),
                            "description": qd.get("description", ""),
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "choiceQuestion": {
                                        "type": "RADIO",
                                        "options": [
                                            {"value": "Accept"},
                                            {"value": "Reject"},
                                            {"isOther": True},
                                        ],
                                        "shuffle": False,
                                    },
                                }
                            },
                        },
                        "location": {"index": i},
                    }
                }
                requests.append(create_request)

        form_body = {"requests": requests}
        forms_service.forms().batchUpdate(
            formId=GOOGLE_FORM_ID, body=form_body
        ).execute()

        st.success("Google Form updated successfully.")
    except HttpError as error:
        st.error(f"An error occurred while updating the form: {error}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")