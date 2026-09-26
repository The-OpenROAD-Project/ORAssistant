#!/bin/bash -eu
# Write the Markdown summary that Secret CI posts for an evaluation run.
#
# Usage: summarize_output.sh OUTPUT SUMMARY
#
# The full output is several hundred KB, far above GitHub's 65536-character
# comment limit, so the summary keeps the aggregate metrics at its end. The
# run metadata line (see run_metadata.py) goes directly above them, so a judge
# or dataset change is visible next to the scores it moved.

output=$1
summary=$2

[ -s "$output" ] || exit 0

metadata=$(grep -o 'Run metadata: .*' "$output" | tail -n 1 || true)
start=$(grep -n 'Aggregate Metrics' "$output" | tail -n 1 | cut -d: -f1 || true)
{
  echo '```text'
  if [ -n "$metadata" ]; then
    echo "$metadata"
  fi
  if [ -n "$start" ]; then
    tail -n +"$((start - 1))" "$output"
  else
    tail -n 100 "$output"
  fi | tail -c 60000
  echo '```'
} > "$summary"
