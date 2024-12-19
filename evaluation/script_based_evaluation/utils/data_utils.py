import csv
from utils.logging_utils import log_error
import traceback


def read_data(csv_file: str) -> list[dict[str, str]]:
    questions = []
    with open(csv_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip the header row
        assert len(header) == 2, "CSV file must have exactly 2 columns"
        for row in reader:
            questions.append(
                {"question": row[0].strip(), "ground_truth": row[1].strip()}
            )
    return questions


def validate_csv_lines(csv_file: str) -> list[dict[str, str]]:
    valid_questions = []
    try:
        with open(csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip the header row
            if header is None or len(header) != 2:
                raise ValueError("CSV file is empty or has an invalid header.")

            for i, row in enumerate(reader, start=2):
                if len(row) == 2 and row[0].strip() and row[1].strip():
                    valid_questions.append(
                        {"question": row[0].strip(), "ground_truth": row[1].strip()}
                    )
    except Exception as e:
        log_error(f"Error in validate_csv_lines: {str(e)}", traceback.format_exc())
        raise

    return valid_questions
