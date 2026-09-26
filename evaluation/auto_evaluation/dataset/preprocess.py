import csv
import json
from typing import Any

# DeepEval 4 flipped HallucinationMetric. Its score is now the share of
# contexts that the answer does not contradict, and a case passes when the
# score is at or above the threshold. DeepEval 3 scored the contradicted
# share, where lower was better. Averages from the two versions are on
# opposite scales, so the summary names the scale it prints.
SCORE_NOTES = {
    "Hallucination": "(share of contexts not contradicted, higher is better)",
}


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


def read_deepeval_cache() -> dict[str, dict[str, float]]:
    """Print the mean score and pass rate of each metric, and return them."""
    import os

    cache_file = ".deepeval/.deepeval-cache.json"
    if not os.path.exists(cache_file):
        print(f"Warning: {cache_file} not found. Skipping cache read.")
        return {}

    metric_scores: dict[str, list[float]] = {
        "Contextual Precision": [],
        "Contextual Recall": [],
        "Hallucination": [],
    }
    metric_passes: dict[str, list[bool]] = {
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
        line = f"{key} {sum(value) / len(value)}"
        if key in SCORE_NOTES:
            line += f" {SCORE_NOTES[key]}"
        print(line)
    print("Metric Passrates: ")
    for key, value in metric_passes.items():
        print(key, value.count(True) / len(value))

    return {
        key: {
            "mean": sum(metric_scores[key]) / len(metric_scores[key]),
            "pass_rate": metric_passes[key].count(True) / len(metric_passes[key]),
        }
        for key in metric_scores
    }


if __name__ == "__main__":
    read_deepeval_cache()
