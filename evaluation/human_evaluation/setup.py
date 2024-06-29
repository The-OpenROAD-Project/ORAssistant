import os
import argparse
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_JSON")

scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/forms",
    "https://www.googleapis.com/auth/spreadsheets",
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
drive_service = build("drive", "v3", credentials=creds)
sheets_service = build("sheets", "v4", credentials=creds)
forms_service = build("forms", "v1", credentials=creds)


def share_file(sheet_id: str, user_email: str) -> None:
    """
    Gives access to the user with the given email other than the service account.

    Args:
    - sheet_id (str): ID of the file to be shared.
    - user_email (str): Email address to share the file with.
    """
    drive_service.permissions().create(
        fileId=sheet_id,
        body={"type": "user", "role": "writer", "emailAddress": user_email},
    ).execute()


def create_google_form(form_title: str, user_email: str) -> str:
    """
    Create a Google Form and share it with the given email.

    Args:
    - form_title (str): Title of the form.
    - user_email (str): Email address to share the form with.

    Returns:
    - str: Google Form ID.
    """
    form_metadata = {"info": {"title": form_title}}
    form = forms_service.forms().create(body=form_metadata).execute()
    form_id = form["formId"]
    print(f"Created Form with ID: {form_id}")

    share_file(form_id, user_email)

    return form_id


def create_google_sheet(sheet_title: str, user_email: str) -> str:
    """
    Create a Google Sheet with columns Questions and Generated Answers, and share it with the given email.

    Args:
    - sheet_title (str): Title of the sheet.
    - user_email (str): Email address to share the sheet with.

    Returns:
    - str: Google Sheet ID.
    """
    sheet_metadata = {"properties": {"title": sheet_title}}
    sheet = sheets_service.spreadsheets().create(body=sheet_metadata).execute()
    sheet_id = sheet["spreadsheetId"]
    print(f"Created Sheet with ID: {sheet_id}")

    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(sheet_id).sheet1
    sheet.append_row(["Questions", "Generated Answers"])

    share_file(sheet_id, user_email)

    return sheet_id


def update_env_file(updates: dict[str, str]) -> None:
    """
    Update settings in .env file with the Sheet ID and Form ID.

    Args:
    - updates (dict[str, str]): Dictionary of updates to be made in the .env file.
    """
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, "w").close()
    with open(env_file, "r") as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        for key, value in updates.items():
            if line.startswith(key):
                line = f"{key}={value}\n"
        new_lines.append(line)

    for key, value in updates.items():
        if f"{key}=" not in "".join(new_lines):
            new_lines.append(f"{key}={value}\n")

    with open(env_file, "w") as file:
        file.writelines(new_lines)

def main() -> None:
    parser = argparse.ArgumentParser(description="Create Google Form and/or Google Sheet, and update .env file.")
    parser.add_argument('--create-form', action='store_true', help='Create a Google Form')
    parser.add_argument('--create-sheet', action='store_true', help='Create a Google Sheet')
    parser.add_argument('--user-email', type=str, required=True, help="Email address to share the created resources with")
    parser.add_argument('--form-title', type=str, default='OR Assistant Feedback Form', help='Title for the Google Form')
    parser.add_argument('--sheet-title', type=str, default='OR Assistant Evaluation Sheet', help='Title for the Google Sheet')

    args = parser.parse_args()

    updates = {}

    if args.create_form:
        form_id = create_google_form(args.form_title, args.user_email)
        print(f"Form created successfully. View form at: https://docs.google.com/forms/d/{form_id}/edit")
        updates["GOOGLE_FORM_ID"] = form_id

    if args.create_sheet:
        sheet_id = create_google_sheet(args.sheet_title, args.user_email)
        print(f"Google Sheet created successfully. View sheet at: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        updates["GOOGLE_SHEET_ID"] = sheet_id

    if updates:
        update_env_file(updates)
        print("The .env file has been updated with the new IDs.")

if __name__ == "__main__":
    main()