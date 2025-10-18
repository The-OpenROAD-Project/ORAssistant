import csv
import json
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


def read_deepeval_cache():
    import os

    cache_file = ".deepeval/.deepeval-cache.json"
    if not os.path.exists(cache_file):
        print(f"Warning: {cache_file} not found. Skipping cache read.")
        return

    metric_scores = {
        "Contextual Precision": [],
        "Contextual Recall": [],
        "Hallucination": [],
    }
    metric_passes = {
        "Contextual Precision": [],
        "Contextual Recall": [],
        "Hallucination": [],
    }
    with open(cache_file) as f:
        results = json.load(f)
    for _, value in results["test_cases_lookup_map"].items():
        for metric in value["cached_metrics_data"]:
            metric_scores[metric["metric_data"]["name"]].append(
                metric["metric_data"]["score"]
            )
            metric_passes[metric["metric_data"]["name"]].append(
                metric["metric_data"]["success"]
            )

    print("Average Metric Scores: ")
    for key, value in metric_scores.items():
        print(key, sum(value) / len(value))
    print("Metric Passrates: ")
    for key, value in metric_passes.items():
        print(key, value.count(True) / len(value))


if __name__ == "__main__":
    read_deepeval_cache()
