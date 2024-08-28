# OpenROAD Retriever Benchmark

This project contains scripts and configuration files for benchmarking different retriever models for the OpenROAD chatbot.

## Files

- `eval_benchmark.py`: The main Python script for running the benchmark tests.
- `.env`: Environment variables configuration (not included in this repository).
- `creds.json`: Google Cloud credentials for accessing Vertex AI (not included in this repository).

## Setup

1. Ensure you have Python 3.7+ installed.
2. Install the required dependencies:
   ```
   pip install vertexai tqdm requests
   ```
3. Set up the `.env` file with necessary environment variables (if required).
4. Place the `creds.json` file in the same directory as the script. This file should contain your Google Cloud service account key for accessing Vertex AI.

## Configuration

The `eval_benchmark.py` script uses the following configuration:

- `USE_CLI_INPUT`: Set to `False` to use predefined constants instead of CLI input.
- `INPUT_FILE`: The CSV file containing questions and ground truth answers.
- `SELECTED_RETRIEVERS`: List of retrievers to test, or `["all"]` for all retrievers. 
- `BASE_URL`: The base URL for the general API.
- `BASE_URL_AGENT_RERANKER`: The base URL for the agent-retriever-reranker API. [if need to test agent retriever reranker]
- `ITERATIONS`: Number of iterations to run for each question.
- `MODEL_NAME`: The name of the Vertex AI model to use (default: "gemini-1.5-pro").

## Running the Benchmark

To run the benchmark:

1. Ensure all configuration files are in place.
2. Run the script:
   ```
   python eval_benchmark.py
   ```
3. If `USE_CLI_INPUT` is `True`, follow the prompts to input necessary information.
4. The script will run the tests and save results to a CSV file.

## Output

The script generates a CSV file with the following columns:

- question
- ground_truth
- retriever_type
- response_time
- response
- tool
- itr (iteration number)
- acc_value (accuracy value)
- llm_score (LLM-based score)
- hall_score (hallucination score)

## Resuming Interrupted Tests

The script supports resuming interrupted tests. It saves progress after each iteration and can pick up where it left off if interrupted.

## Security Note

The `creds.json` file contains sensitive information. Ensure it is not committed to version control and is properly secured.
