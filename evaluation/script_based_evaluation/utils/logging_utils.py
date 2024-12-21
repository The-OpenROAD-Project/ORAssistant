from datetime import datetime


def log_error(error_message: str, error_details: str):
    with open("logs/error_log.txt", "a") as f:
        f.write(f"{datetime.now()}: {error_message}\n")
        f.write(f"Details:\n{error_details}\n\n")
