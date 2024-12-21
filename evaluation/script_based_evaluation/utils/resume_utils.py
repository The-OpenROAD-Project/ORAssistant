import json
import traceback
from typing import Any
from script_based_evaluation.utils.logging_utils import log_error


def initialize_resume_data() -> dict[str, Any]:
    return {"retriever": "", "question": "", "iteration": 0}


def save_resume_data(resume_data: dict[str, Any], filename: str):
    with open(filename, "w") as f:
        json.dump(resume_data, f)


def load_resume_data(filename: str) -> dict[str, Any]:
    try:
        with open(filename, "r") as f:
            return dict(json.load(f))
    except FileNotFoundError:
        return initialize_resume_data()
    except Exception as e:
        log_error(f"Error in load_resume_data: {str(e)}", traceback.format_exc())
        raise
