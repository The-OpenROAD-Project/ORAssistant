import json
from deepeval.test_case import LLMTestCase
from .quality_agents import (
    GroundednessMetric,
    QuestionRelevanceMetric,
    QuestionStandaloneMetric
)


json_path = "data/generated_qa_pairs_gemini_pro_new.json"

# Loading questions
with open(json_path, "r") as f:
    qa_pairs = json.load(f)

# Initializing metrics
groundedness_metric = GroundednessMetric()
relevance_metric = QuestionRelevanceMetric()
standalone_metric = QuestionStandaloneMetric()


for entry in qa_pairs:
    question = entry["question"]
    answer = entry["answer"]
    context = entry["context"]
    
    test_case_question = LLMTestCase(input=question,actual_output="", context=[context])
    
    groundedness_score = groundedness_metric.measure(test_case_question)
    relevance_score = relevance_metric.measure(test_case_question)
    standalone_score = standalone_metric.measure(test_case_question)
    
    print(f"Question: {question}")
    print(f"  Groundedness: {groundedness_score:.2f} ({groundedness_metric.reason})")
    print(f"  Relevance: {relevance_score:.2f} ({relevance_metric.reason})")
    print(f"  Standalone: {standalone_score:.2f} ({standalone_metric.reason})")
    print("-" * 60)
    break
