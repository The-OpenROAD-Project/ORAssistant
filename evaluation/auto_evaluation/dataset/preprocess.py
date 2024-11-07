import csv
from typing import Any


def read_data(csv_file: str) -> list[dict]:
    questions = []
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip the header row
        assert len(header) == 2, "CSV file must have exactly 2 columns"
        for row in reader:
            questions.append(
                {"question": row[0].strip(), "ground_truth": row[1].strip()}
            )
    return questions


def write_data(results_list: list[dict[str, Any]], results_path: str):
    keys = results_list[0].keys()
    with open(results_path, "w") as f:
        writer = csv.writer(f)
        writer.writerow(list(keys))
        for result in results_list:
            writer.writerow([result[key] for key in keys])
    print(f"Results written to {results_path}")
