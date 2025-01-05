# ORAssistant Automated Evaluation

This project automates the evaluation of language model responses using classification-based metrics and LLMScore. It supports testing against various models, including OpenAI and Google Vertex AI. It also serves as an evaluation benchmark for comparing multiple versions of ORAssistant.


## Features

1. **Classification-based Metrics**: 
   - Categorizes responses into True Positive (TP), True Negative (TN), False Positive (FP), and False Negative (FN).
   - Computes metrics such as Accuracy, Precision, Recall, and F1 Score.

2. **LLMScore**: 
   - Assigns a score between 0 and 1 by comparing the ground truth against the generated response's quality and accuracy.

## Setup

### Environment Variables

Create a `.env` file in the root directory with the following variables:
```plaintext
GOOGLE_APPLICATION_CREDENTIALS=path/to/secret.json
OPENAI_API_KEY=your_openai_api_key  # Required if testing against OpenAI models
```
### Required Files

- `secret.json`: Ensure you have a Google Vertex AI subscription and the necessary credentials file.

### Data Files

- **Input File**: `data/data.csv`
  - This file should contain the questions to be tested. Ensure it is formatted as a CSV file with the following columns: `Question`, `Answer`.

- **Output File**: `data/data_result.csv`
  - This file will be generated after running the script. It contains the results of the evaluation.

## How to Run

1. **Activate virtual environment**

   From the previous directory (`evaluation`), make sure you have run the command
   `make init` before activating virtual environment. It is needed to recognise
   this folder as a submodule.

2. **Run the Script**

   Use the following command to execute the script with customizable options:

   ```bash
   python script.py --env-path /path/to/.env --creds-path /path/to/secret.json --iterations 10 --llms "base-gemini-1.5-flash,base-gpt-4o" --agent-retrievers "v1=http://url1.com,v2=http://url2.com"
   ```

   - `--env-path`: Path to the `.env` file.
   - `--creds-path`: Path to the `secret.json` file.
   - `--iterations`: Number of iterations per question.
   - `--llms`: Comma-separated list of LLMs to test.
   - `--agent-retrievers`: Comma-separated list of agent-retriever names and URLs.

3. **View Results**

   Results will be saved in a CSV file named after the input data file with `_result` appended.

## Basic Usage

### a. Default Usage

```bash
python main.py
```

- Uses the default `.env` file in the project root.
- Default `data/data.csv` as input.
- 5 iterations per question.
- Tests all available LLMs.
- No additional agent-retrievers.

### b. Specify .env and secret.json Paths

```bash
python main.py --env-path /path/to/.env --creds-path /path/to/secret.json
```

### c. Customize Iterations and Select Specific LLMs

```bash
python main.py --iterations 10 --llms "base-gpt-4o,base-gemini-1.5-flash"
```

### d. Add Agent-Retrievers with Custom Names

```bash
python main.py --agent-retrievers "v1=http://url1.com,v2=http://url2.com"
```

### e. Full Example with All Options

```bash
python main.py \
    --env-path /path/to/.env \
    --creds-path /path/to/secret.json \
    --iterations 10 \
    --llms "base-gemini-1.5-flash,base-gpt-4o" \
    --agent-retrievers "v1=http://url1.com,v2=http://url2.com"
```

### f. Display Help Message

To view all available command-line options:

```bash
python main.py --help
```

### Run Analysis 

After generating results, you can perform analysis using the provided `analysis.py` script. To run the analysis, execute the following command:

```bash
streamlit run analysis.py
```


### Sample Comparison Commands

1. To compare three versions of ORAssistant, use:
   ```bash
   python main.py --agent-retrievers "orassistant-v1=http://url1.com,orassistant-v2=http://url2.com,orassistant-v3=http://url3.com"
   ```
   *Note: Each URL is the endpoint of the ORAssistant backend.*

2. To compare ORAssistant with base-gpt-4o, use:
   ```bash
   python main.py --llms "base-gpt-4o" --agent-retrievers "orassistant=http://url.com"
   ```
   *Note: The URL is the endpoint of the ORAssistant backend.*