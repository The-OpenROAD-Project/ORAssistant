import argparse
import sys
import os
import csv
import traceback
import time
from script_based_evaluation.utils.data_utils import validate_csv_lines
from script_based_evaluation.utils.api_utils import send_request, llm_judge
from script_based_evaluation.utils.logging_utils import log_error
from script_based_evaluation.config.config import load_environment
from openai import OpenAI
from tqdm import tqdm
from typing import Any
import vertexai


def get_accuracy_value(response_text: str, ground_truth: str, query_text: str) -> str:
    sys_prompt = """
    You are a LLM Judge Evaluator for OpenROAD Chat Bot. All Questions and Answers should be technical and related to OpenROAD, Chip Design, Problems related to it, general query, commands.
    Evaluate the response based on the ground truth and return one of the following: TP, TN, FP, FN.
    Definitions:
    True Positive (TP): The model provided a correct and relevant answer. If the response is partially correct, it should still be considered TP.
    True Negative (TN): The model correctly identified that it couldn't answer a question or that the question was out of scope.
    False Positive (FP): The model provided an answer that it thought was correct, but was actually incorrect or irrelevant. (NOTE: Mark TP even if it's partially correct, FP is only for completely incorrect or irrelevant answer)
    False Negative (FN): The model failed to provide an answer when it should have been able to.
    Instructions: Compare the model's response with the ground truth. If the model's response is accurate and relevant, return 'TP'.
    If the model correctly identifies that it cannot answer or the question is out of scope, return 'TN'.
    If the model's response is incorrect or irrelevant, return 'FP'.
    If the model fails to provide an answer when it should have been able to, return 'FN'.
    Provide only one of the following outputs: TP, FP, FN, TN.
    return type [one word only] for ex: TP
    """
    final_query = f"{sys_prompt}\nQUESTION= {query_text}, ANS= {response_text}, GT= {ground_truth}"
    for attempt in range(5):
        try:
            result = llm_judge(final_query)
            print("Accuracy evaluation result:", result)
            if result.strip() in ["TP", "TN", "FP", "FN"]:
                return result.strip()
            else:
                raise ValueError(f"Invalid accuracy evaluation result: {result}")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == 4:
                print(f"All attempts failed. Raw accuracy value: {result}")
                raise ValueError(
                    f"Failed to process accuracy value after 5 attempts: {str(e)}"
                )
            time.sleep(2)

    return "Something went wrong while getting accuracy_value"


def get_llm_score(response_text: str, ground_truth: str, query_text: str) -> Any:
    sys_prompt = """RULE: return type [float]  Evaluate the response's accuracy by comparing it to the ground truth answer. Assign a numerical value between 0.00 and 1.00, where 0.00 represents completely inaccurate and 1.00 represents exactly accurate. If the response fails to provide a correct answer, contains apologies such as 'sorry,' or states 'it's not in my context,' assign a score of 0.00
    Your response must be a single float number between 0.00 and 1.00, with two decimal places. Do not include any other text or explanation.

Example outputs:
0.00
0.75
1.00
    """
    final_query = f"{sys_prompt}\nQUESTION= {query_text}, ANS= {response_text}, GT= {ground_truth}"
    for attempt in range(5):
        try:
            result = llm_judge(final_query)
            print("LLM score result:", result)
            score = float(result.strip())
            if 0.00 <= score <= 1.00:
                return score
            else:
                raise ValueError(f"Invalid LLM score result: {result}")
        except ValueError as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == 4:
                print(f"All attempts failed. Raw LLM score value: {result}")
                raise ValueError(
                    f"Failed to process LLM score after 5 attempts: {str(e)}"
                )
            time.sleep(2)
    return "Something went wrong while getting llm_score"


def check_hallucination(response_text: str, ground_truth: str, query_text: str) -> Any:
    prompt = f"""
    Task: Check for hallucination
    Question: {query_text}
    Response: {response_text}
    Ground Truth: {ground_truth}
    Task: Determine if the response is unrelated or significantly deviates from the ground truth.
    Return "True" if the response is completely different or unrelated to the ground truth. Otherwise, return "False".
    """
    for attempt in range(5):
        try:
            result = llm_judge(prompt)
            print("Hallucination check result:", result)
            if result.strip() in ["True", "False"]:
                return result.strip() == "True"
            else:
                raise ValueError(f"Invalid hallucination result: {result}")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == 4:
                print(f"All attempts failed. Raw hallucination value: {result}")
                raise ValueError(
                    f"Failed to process hallucination value after 5 attempts: {str(e)}"
                )
            time.sleep(2)
    return "Something went wrong while getting check_hallucination"


def append_result_to_csv(result: dict[str, object], output_file: str):
    fieldnames = [
        "question",
        "ground_truth",
        "architecture",
        "response_time",
        "response",
        "itr",
        "acc_value",
        "llm_score",
        "hall_score",
    ]
    try:
        file_exists = os.path.isfile(output_file)
        with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)
    except Exception as e:
        error_message = f"Error in append_result_to_csv: {str(e)}"
        log_error(error_message, traceback.format_exc())
        print(f"{error_message}\nCheck logs/error_log.txt for details.")
        sys.exit(1)


def run_tests(
    questions: list[dict[str, str]],
    selected_retrievers: list[str],
    iterations: int,
    output_file: str,
    agent_retriever_urls: dict[str, str],
    client: OpenAI,
):
    total_iterations = len(questions) * len(selected_retrievers) * iterations
    print("Total Iterations:", total_iterations)
    # Create a progress bar
    pbar = tqdm(total=total_iterations)

    for question in questions:
        prompt = question["question"]
        ground_truth = question["ground_truth"]

        for architecture in selected_retrievers:
            for itr in range(1, iterations + 1):
                print(
                    f"Testing question: {prompt} with architecture: {architecture}, iteration: {itr}"
                )
                try:
                    response, response_time = send_request(
                        architecture, prompt, agent_retriever_urls, client
                    )
                    if not response:
                        response = "No response received."

                    acc_value = get_accuracy_value(response, ground_truth, prompt)
                    llm_score = get_llm_score(response, ground_truth, prompt)
                    hallucination = check_hallucination(response, ground_truth, prompt)

                    result = {
                        "question": prompt,
                        "ground_truth": ground_truth,
                        "architecture": architecture,
                        "response_time": response_time,
                        "response": response,
                        "itr": itr,
                        "acc_value": acc_value,
                        "llm_score": llm_score,
                        "hall_score": hallucination,
                    }

                    append_result_to_csv(result, output_file)

                except Exception as e:
                    error_message = f"Error in run_tests: {str(e)}"
                    log_error(error_message, traceback.format_exc())
                    print(f"{error_message}\nCheck logs/error_log.txt for details.")

                pbar.update(1)

    pbar.close()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test LLM responses and evaluate them."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations per question per retriever",
    )
    parser.add_argument(
        "--llms", type=str, default="", help="Comma-separated list of LLMs to test"
    )
    parser.add_argument(
        "--agent-retrievers",
        type=str,
        default="",
        help="Comma-separated list of agent-retriever names and URLs in the format name=url",
    )
    args = parser.parse_args()

    iterations = args.iterations

    selected_retrievers = []
    if args.llms:
        selected_retrievers = [llm.strip() for llm in args.llms.split(",")]

    agent_retriever_urls = {}
    if args.agent_retrievers:
        for item in args.agent_retrievers.split(","):
            if "=" in item:
                name, url = item.split("=", 1)
                name = name.strip()
                url = url.strip()
                if not name or not url:
                    print(
                        f"Invalid format for agent-retriever: '{item}'. Expected format 'name=url'."
                    )
                    sys.exit(1)
                agent_retriever_urls[name] = url
            else:
                print(
                    f"Invalid format for agent-retriever: '{item}'. Expected format 'name=url'."
                )
                sys.exit(1)

    # Merge selected_retrievers with agent_retriever names
    if agent_retriever_urls:
        selected_retrievers.extend(agent_retriever_urls.keys())

    # Initialize environment
    load_environment(".env")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Initialize Vertex AI
    vertexai.init()

    # Input and Output Files
    input_file = "data/data.csv"
    output_file = f"{os.path.splitext(input_file)[0]}_result.csv"

    # Validate and read questions
    valid_questions = validate_csv_lines(input_file)

    if not valid_questions:
        print("Error: No valid questions found in the CSV file.")
        sys.exit(1)

    print("\nQuestions to be tested:")
    for i, question in enumerate(valid_questions, start=1):
        print(f"{i}. {question['question']}")

    input("\nPress Enter to start testing...")

    # Run the tests
    try:
        run_tests(
            valid_questions,
            selected_retrievers,
            iterations,
            output_file,
            agent_retriever_urls,
            client,
        )
        print(f"\nTesting completed. Results saved to {output_file}")
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        log_error(error_message, traceback.format_exc())
        print(f"{error_message}\nCheck logs/error_log.txt for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
