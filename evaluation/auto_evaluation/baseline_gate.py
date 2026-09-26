"""
Fail a run whose scores fall too far below the last master baseline.

Secret CI runs this after the evaluation, with the run's results file and the
results file of the newest completed master run (see run_results.py for the
schema). Run-to-run noise is about 3 points, so a drop of more than MARGIN in
the precision or recall pass rate fails the run.

The gate skips, with a notice, when there is no baseline, when either run has
no scores, or when the judge or the dataset differs: scores from a different
judge or dataset are on a different scale.

Usage: python baseline_gate.py --current CURRENT.json [--baseline BASELINE.json]
The script uses only the standard library, so it runs without the project
environment. Output lines that start with "::" are GitHub annotations.
"""

import argparse
import json
from dataclasses import dataclass, field

# Largest allowed drop in pass rate, as a fraction: 0.05 is 5 points.
MARGIN = 0.05
GATED_METRICS = ("Contextual Precision", "Contextual Recall")
SAME_SCALE_FIELDS = ("judge", "dataset")
# Pass rates are multiples of 1/test_count, so a drop of exactly MARGIN can
# come out a little larger in floating point.
_EPSILON = 1e-9


@dataclass
class Verdict:
    passed: bool = True
    skipped: bool = False
    lines: list[str] = field(default_factory=list)


def _skip(reason: str) -> Verdict:
    return Verdict(skipped=True, lines=[f"Baseline gate skipped: {reason}."])


def compare(current: dict, baseline: dict | None, margin: float = MARGIN) -> Verdict:
    """Compare two results files. baseline is None when none was found."""
    if baseline is None:
        return _skip("no completed master run with a results file")
    for name, results in (("current run", current), ("baseline", baseline)):
        if results.get("status") != "completed" or not results.get("metrics"):
            return _skip(f"the {name} has no scores")
    for key in SAME_SCALE_FIELDS:
        now = current["metadata"].get(key)
        then = baseline["metadata"].get(key)
        if now != then:
            return _skip(f"{key} {now} differs from the baseline {key} {then}")

    verdict = Verdict(
        lines=[f"Baseline: orassistant {baseline['metadata'].get('orassistant')}"]
    )
    for metric in GATED_METRICS:
        now = current["metrics"].get(metric, {}).get("pass_rate")
        then = baseline["metrics"].get(metric, {}).get("pass_rate")
        if now is None or then is None:
            verdict.lines.append(f"{metric} pass rate: skipped, no value in both runs")
            continue
        delta = now - then
        failed = delta < -margin - _EPSILON
        verdict.passed = verdict.passed and not failed
        verdict.lines.append(
            f"{metric} pass rate: baseline {then:.2f}, current {now:.2f}, "
            f"delta {delta:+.2f} (limit -{margin:.2f}) {'FAIL' if failed else 'ok'}"
        )
    return verdict


def _load(path: str) -> dict:
    with open(path) as f:
        results: dict = json.load(f)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--current", required=True)
    parser.add_argument("--baseline")
    args = parser.parse_args(argv)

    baseline = _load(args.baseline) if args.baseline else None
    verdict = compare(_load(args.current), baseline)
    for line in verdict.lines:
        print(line)
    if verdict.skipped:
        print(f"::notice::{verdict.lines[0]}")
    elif not verdict.passed:
        print(
            f"::error::A pass rate fell more than {MARGIN:.2f} below the "
            "last master baseline."
        )
    return 0 if verdict.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
