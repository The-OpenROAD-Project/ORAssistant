"""
Print the per-metric delta between two results files.

Use it before a judge change: run the evaluation on one commit with the old
and the new judge, and compare the two eval_results.json files (see "Judge
change" in the README). The delta shows how far the new judge moves each
score, so later runs are not read as a code regression.

Usage: python compare_results.py OLD.json NEW.json
The exit code is 1 when the two runs used a different commit or dataset,
because the delta then mixes a judge change with other changes.
"""

import argparse
import json

# Fields that must match, so that only the judge differs.
SAME_RUN_FIELDS = ("orassistant", "dataset")


def compare(old: dict, new: dict) -> tuple[list[str], bool]:
    """Return the report lines, and whether both runs used one commit and dataset."""
    for name, results in (("old", old), ("new", new)):
        if results.get("status") != "completed" or not results.get("metrics"):
            raise ValueError(f"the {name} run has no scores")

    lines = [f"Judge: {old['metadata'].get('judge')} -> {new['metadata'].get('judge')}"]
    same_run = True
    for key in SAME_RUN_FIELDS:
        before, after = old["metadata"].get(key), new["metadata"].get(key)
        if before != after:
            same_run = False
            lines.append(f"Different {key}: {before} -> {after}")

    for metric in sorted(old["metrics"].keys() | new["metrics"].keys()):
        before, after = old["metrics"].get(metric), new["metrics"].get(metric)
        if not before or not after:
            lines.append(f"{metric}: missing in one run")
            continue
        parts = [
            f"{label} {before[key]:.2f} -> {after[key]:.2f} "
            f"({after[key] - before[key]:+.2f})"
            for label, key in (("mean", "mean"), ("pass rate", "pass_rate"))
        ]
        lines.append(f"{metric}: {', '.join(parts)}")
    return lines, same_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("old")
    parser.add_argument("new")
    args = parser.parse_args(argv)

    with open(args.old) as f:
        old = json.load(f)
    with open(args.new) as f:
        new = json.load(f)
    lines, same_run = compare(old, new)
    print("\n".join(lines))
    return 0 if same_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
