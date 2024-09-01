import os
import csv
from typing import List, Dict, Any
from tqdm import tqdm
import requests
import time
import json
from vertexai import init as vertexai_init
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use environment variables
BASE_URL = os.getenv('ENDPOINT1')
BASE_URL_AGENT_RERANKER = os.getenv('ENDPOINT2')
INPUT_FILE = os.getenv('input_file_path', 'data.csv')  # Use 'data.csv' as default if not specified

# Configuration constants
USE_CLI_INPUT = True # Set to False to use the constants below instead of CLI input

# If USE_CLI_INPUT is False, the following constants will be used
SELECTED_RETRIEVERS = ["all"]  # or use ["all"] for all retrievers
ITERATIONS = 1

# Default LLM model configuration
MODEL_NAME = "gemini-1.5-pro"
generation_config = {
    "temperature": 0,
    "response_mime_type": "text/plain",
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
}

# Set up the environment variable to point to your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"

# Initialize Vertex AI with default settings
vertexai_init()

# List of all available retrievers
ALL_RETRIEVERS = [
    "agent-retriever",
    "agent-retriever-reranker",
    "hybrid",
    "sim",
    "ensemble"
]

def read_data(csv_file: str):
    questions = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip the header row
        assert len(header) == 2, "CSV file must have exactly 2 columns"
        for row in reader:
            questions.append({
                "question": row[0].strip(),
                "ground_truth": row[1].strip()
            })
    return questions

def send_request(endpoint: str, query: str, base_url: str):
    url = f"{base_url}{endpoint}"
    payload = {
        "query": query,
        "list_context": True,
        "list_sources": True
    }
    response = requests.post(url, json=payload)
    return response.json(), response.elapsed.total_seconds() * 1000

def gemini_api_call(model, final_query, max_retries=1):
   
    for attempt in range(1, max_retries + 1):
        try:
            result = model.generate_content(
                final_query
            )
            return result.text.strip()
        except Exception as e:
            if attempt < max_retries:
                print(f"RERUN {attempt}")
                time.sleep(5)
            else:
                print(f"Error: Unable to get a response from Gemini API after {max_retries} attempts. Error details: {str(e)}")
                return None

def get_accuracy_value(response: str, ground_truth: str, query: str) -> str:
    sys_prompt = """
    You are a LLM Judge Evaluator for OpenROAD Chat Bot. All Questions and Answers should be technical and related to OpenROAD, Chip Design, Problems related to it, general query, commands. 
    Evaluate the response based on the ground truth and return one of the following: TP, TN, FP, FN. 
    Definitions: 
    True Positive (TP): The model provided a correct and relevant answer.  If the response is partially correct, it should still be considered TP.
    True Negative (TN): The model correctly identified that it couldn't answer a question or that the question was out of scope. 
    False Positive (FP): The model provided an answer that it thought was correct, but was actually incorrect or irrelevant. (NOTE: Mark TP even if its partially correct, FP is only for completely incorrect or irrelevant answer)
    False Negative (FN): The model failed to provide an answer when it should have been able to. 
    Instructions: Compare the model's response with the ground truth. If the model's response is accurate and relevant, return 'TP'. 
    If the model correctly identifies that it cannot answer or the question is out of scope, return 'TN'. 
    If the model's response is incorrect or irrelevant, return 'FP'. 
    If the model fails to provide an answer when it should have been able to, return 'FN'. 
    Provide only one of the following outputs: TP, FP, FN, TN.
    return type [one word only] for ex: TP
    """
    final_query = f"{sys_prompt}\nQUESTION= {query}, ANS= {response}, GT= {ground_truth}"
    
    model = GenerativeModel(model_name=MODEL_NAME, generation_config=generation_config, safety_settings=safety_settings)
    result = gemini_api_call(model, final_query)
    return result.strip() if result is not None else "TP"  # Default to TP on error

def get_llm_score(response: str, ground_truth: str, query: str) -> float:
    sys_prompt = """RULE: return type [float]  Evaluate the response's accuracy by comparing it to the ground truth answer. Assign a numerical value between 0.00 and 1.00, where 0.00 represents completely inaccurate and 1.00 represents exactly accurate. If the response fails to provide a correct answer, contains apologies such as 'sorry,' or states 'it's not in my context,' assign a score of 0.00
    Your response must be a single float number between 0.00 and 1.00, with two decimal places. Do not include any other text or explanation.

Example outputs:
0.00
0.75
1.00
    """
    final_query = f"{sys_prompt}\nQUESTION= {query}, ANS= {response}, GT= {ground_truth}"
    
    model = GenerativeModel(model_name=MODEL_NAME, generation_config=generation_config,  safety_settings=safety_settings)
    result = gemini_api_call(model, final_query)
    return float(result) if result is not None else 0.5  # Default to 0.5 on error

def check_hallucination(response: str, ground_truth: str, query: str) -> bool:
    sys_prompt = """Evaluate the response to determine if the model is hallucinating by comparing it to the ground truth answer. Assign a bool value, where false indicates hallucination (very incorrect answer etc rather than saying it doesn't know, it makes a fake answer) and true indicates no hallucination (correct answer, stating it doesn't have the answer and is honest, or reasonably correct answer). Provide only one of the following outputs: true or false. return type [bool] strictly
    our response must be either 'true' or 'false':
- 'false' indicates hallucination (very incorrect answer or making up information)
- 'true' indicates no hallucination (correct answer, stating it doesn't have the answer, or reasonably correct answer)

Respond with only 'true' or 'false', without any other text or explanation.
    """
    final_query = f"{sys_prompt}\nQUESTION= {query}, ANS= {response}, GT= {ground_truth}"
    
    model = GenerativeModel(model_name=MODEL_NAME, generation_config=generation_config,  safety_settings=safety_settings)
    result = gemini_api_call(model, final_query)
    return result.lower() == 'true' if result is not None else True  # Default to True on error

def append_result_to_csv(result: Dict[str, Any], output_file: str):
    fieldnames = ['question', 'ground_truth', 'retriever_type', 'response_time', 'response', 'tool', 'itr', 'acc_value', 'llm_score', 'hall_score']
    
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)

def initialize_resume_data():
    return {"retriever": "", "question": "", "iteration": 0}

def save_resume_data(resume_data, filename):
    with open(filename, 'w') as f:
        json.dump(resume_data, f)

def load_resume_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return initialize_resume_data()

def get_last_processed_state(output_file):
    try:
        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                retriever_type = last_row['retriever_type']
                iteration = int(last_row['itr'])
                
                # Extract question number and text
                question_parts = last_row['question'].split('.', 1)
                question_number = int(question_parts[0].strip())
                question_text = question_parts[1].strip() if len(question_parts) > 1 else question_parts[0].strip()
                
                return retriever_type, iteration, question_number, question_text
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Error reading last state from CSV: {str(e)}")
    return None, 0, 0, ""

def run_tests(questions: List[Dict[str, Any]], selected_retrievers: List[str], base_url: str, base_url_agent_reranker: str, iterations: int, output_file: str, resume_data: Dict[str, Any]):
    results = []
    
    start_retriever_index = selected_retrievers.index(resume_data["retriever"]) if resume_data["retriever"] in selected_retrievers else 0
    
    for retriever in selected_retrievers[start_retriever_index:]:
        print(f"\nTesting retriever: {retriever}")
        
        start_question_index = next((i for i, q in enumerate(questions) if q['question'] == resume_data["question"]), 0)
        
        for i, question in enumerate(tqdm(questions[start_question_index:]), start=start_question_index):
            question_text = question['question']
            
            print(f"\n{i+1}/{len(questions)}")
            print(f"Question: {question_text}")
            print(f"Retriever being tested: {retriever}")
            
            start_iteration = resume_data["iteration"] + 1 if question_text == resume_data["question"] else 1
            
            for itr in range(start_iteration, iterations + 1):
                print(f"Iteration: {itr}/{iterations}")
                print("Awaiting response from endpoint (loading ====)")
                
                if retriever == "agent-retriever-reranker":
                    current_base_url = base_url_agent_reranker
                    endpoint = "/graphs/agent-retriever"
                else:
                    current_base_url = base_url
                    endpoint = f"/graphs/{retriever}" if retriever == "agent-retriever" else f"/chains/{retriever}"
                
                try:
                    response, response_time = send_request(endpoint, question_text, current_base_url)
                    
                    print(f"Response time: {response_time:.2f} ms")
                    
                    result = {
                        'question': f"{i+1}. {question_text}",
                        'ground_truth': question['ground_truth'],
                        'retriever_type': retriever,
                        'response_time': response_time,
                        'response': response['response'],
                        'tool': retriever,
                        'itr': itr,
                        'acc_value': get_accuracy_value(response['response'], question['ground_truth'], question_text),
                        'llm_score': get_llm_score(response['response'], question['ground_truth'], question_text),
                        'hall_score': check_hallucination(response['response'], question['ground_truth'], question_text)
                    }
                    results.append(result)
                    
                    # Update CSV after each call
                    append_result_to_csv(result, output_file)
                    
                    # Update resume data only after successful CSV write
                    resume_data = {
                        "retriever": retriever,
                        "question": question_text,
                        "iteration": itr
                    }
                    save_resume_data(resume_data, f"{output_file}_resume.json")
                except Exception as e:
                    print(f"Error occurred: {str(e)}")
                    print("Saving progress and continuing...")
                    
                    result = {
                        'question': f"{i+1}. {question_text}",
                        'ground_truth': question['ground_truth'],
                        'retriever_type': retriever,
                        'response_time': -1,
                        'response': f"Error: {str(e)}",
                        'tool': retriever,
                        'itr': itr,
                        'acc_value': "ERROR", # "ERROR" is default value for error
                        'llm_score': -1, # -1 is default value for error
                        'hall_score': None # None is default value for error
                    }
                    results.append(result)
                    append_result_to_csv(result, output_file)
                
            # Reset iteration after finishing each question
            resume_data["iteration"] = 0
        
        # Reset question after finishing each retriever
        resume_data["question"] = ""
    
    return results

def main():
    print("Welcome to the Retriever Testing CLI!")
    
    if USE_CLI_INPUT:
        # Ask for input data file path
        while True:
            input_file = input("Enter the path to the input CSV file (e.g., data/questions.csv): ").strip()
            if os.path.exists(input_file) and input_file.lower().endswith('.csv'):
                break
            else:
                print("File not found or not a CSV file. Please enter a valid CSV file path.")
        
        print("Available retrievers:")
        for i, retriever in enumerate(ALL_RETRIEVERS, 1):
            print(f"{i}. {retriever}")
        
        while True:
            selection = input("Enter the numbers of the retrievers you want to test (comma-separated), or 'all' for all retrievers: ")
            if selection.lower() == 'all':
                selected_retrievers = ALL_RETRIEVERS
                break
            try:
                selected_indices = [int(x.strip()) for x in selection.split(',')]
                selected_retrievers = [ALL_RETRIEVERS[i-1] for i in selected_indices if 1 <= i <= len(ALL_RETRIEVERS)]
                if selected_retrievers:
                    break
                else:
                    print("No valid retrievers selected. Please try again.")
            except ValueError:
                print("Invalid input. Please enter comma-separated numbers or 'all'.")
        
        print(f"Selected retrievers: {', '.join(selected_retrievers)}")
        
        base_url = input(f"Enter the base URL for the general API (default: {BASE_URL}): ").strip() or BASE_URL
        
        base_url_agent_reranker = BASE_URL_AGENT_RERANKER
        
        base_url_agent_reranker = ""
        base_url_agent_reranker = ""
        if "agent-retriever-reranker" in selected_retrievers:
            base_url_agent_reranker = input(f"Enter the base URL for agent-retriever-reranker (default: {BASE_URL_AGENT_RERANKER}): ").strip() or BASE_URL_AGENT_RERANKER
        multiple_iterations = input("Do you want to run multiple iterations for each question? (yes/no): ").strip().lower()
        iterations = ITERATIONS if multiple_iterations == 'yes' else 1
    else:
        input_file = INPUT_FILE
        selected_retrievers = ALL_RETRIEVERS if SELECTED_RETRIEVERS == ["all"] else SELECTED_RETRIEVERS
        base_url = BASE_URL
        base_url_agent_reranker = BASE_URL_AGENT_RERANKER if "agent-retriever-reranker" in selected_retrievers else ""
        iterations = ITERATIONS
    
    output_file = f"{os.path.splitext(input_file)[0]}_result.csv"
    resume_file = f"{output_file}_resume.json"
    
    if os.path.exists(resume_file):
        print("BACKUP FOUND")
        resume_choice = input("Do you want to resume from the previous run? (yes/no): ").strip().lower()
        if resume_choice == 'yes':
            resume_data = load_resume_data(resume_file)
            print("Resuming from previous state...")
        else:
            print("Starting fresh. Previous backup will be overwritten.")
            resume_data = initialize_resume_data()
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(resume_file):
                os.remove(resume_file)
    else:
        print("No previous backup found. Starting fresh.")
        resume_data = initialize_resume_data()

    input("Press Enter to start testing...")
    
    questions = read_data(input_file)
    results = run_tests(questions, selected_retrievers, base_url, base_url_agent_reranker, iterations, output_file, resume_data)
    
    print(f"\nTesting completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()