import os
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from dotenv import load_dotenv

load_dotenv()

if not os.getenv('GOOGLE_CREDENTIALS_JSON'):
    raise ValueError(
        'The GOOGLE_CREDENTIALS_JSON environment variable is not set or is empty.'
    )
if not os.getenv('GOOGLE_SHEET_ID'):
    raise ValueError('The GOOGLE_SHEET_ID environment variable is not set or is empty.')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_CREDENTIALS_JSON')
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_QUESTIONS = 'A2:A'
RANGE_ANSWERS = 'B2:B'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
service = build('sheets', 'v4', credentials=creds)


def read_questions_and_answers() -> tuple[list[str], int]:
    """
    Read questions from the Google Sheet.

    Returns:
    - Tuple containing a list of questions and the count of questions.
    """
    try:
        sheet = service.spreadsheets()
        result_questions = (
            sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_QUESTIONS).execute()
        )
        values_questions = result_questions.get('values', [])
        questions = [row[0] for row in values_questions]
        question_count = len(questions)

        return questions, question_count
    except HttpError as error:
        st.error('Rate Limited! Please try again after a few seconds.')
        st.error(f'An error occurred: {error}')
        return [], 0


def find_new_questions(question_count: int) -> list[int]:
    """
    Find rows with no answers in the Google Sheet.

    Args:
    - question_count (int): The total number of questions.

    Returns:
    - List of row numbers where answers are empty.
    """
    try:
        range_ = f'A2:B{question_count + 1}'
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=range_).execute()
        values = result.get('values', [])
        empty_answer_rows = []
        for i, row in enumerate(values, start=2):
            if len(row) < 2 or not row[1]:
                empty_answer_rows.append(i)
        return empty_answer_rows
    except HttpError as error:
        st.error('Rate Limited! Please try again after a few seconds.')
        st.error(f'An error occurred: {error}')
        return []


def write_responses(responses: list[str], row_numbers: list[int]) -> int:
    """
    Write generated responses back to the Google Sheet.

    Args:
    - responses (list[str]): List of generated responses.
    - row_numbers (list[int]): List of row numbers corresponding to the responses.

    Returns:
    - The total number of cells updated.
    """
    try:
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.get_worksheet(0)

        # Format the header if it is empty
        if not sheet.row_values(1):
            sheet.format('A1:B1', {'textFormat': {'bold': True}})
            sheet.update_cell(1, 1, 'Questions')
            sheet.update_cell(1, 2, 'Generated Answers')

        body = {
            'valueInputOption': 'RAW',
            'data': [
                {'range': f'B{row}', 'values': [[response]]}
                for row, response in zip(row_numbers, responses)
            ],
        }
        result = (
            service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=SHEET_ID, body=body)
            .execute()
        )
        return result.get('totalUpdatedCells')
    except HttpError as error:
        st.error('Failed to write responses to the Google Sheet.')
        st.error(f'An error occurred: {error}')
        return 0
