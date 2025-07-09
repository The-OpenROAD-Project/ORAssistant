import sys
from pathlib import Path
from dotenv import load_dotenv


src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from langchain_google_genai import ChatGoogleGenerativeAI
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

load_dotenv()

# Groundedness critique prompt template
question_groundedness_critique_prompt = """
You are an expert evaluator tasked with assessing the groundedness of a question-answer pair.

Your task is to evaluate whether the given question is well-grounded in the provided context.
A well-grounded question should:
1. Be answerable using information from the context
2. Not require external knowledge beyond the context
3. Be specific and factual rather than speculative
4. Have clear supporting evidence in the context

Please analyze the question and context, then provide a rating from 1 to 5:
- 1: Completely ungrounded - question cannot be answered from context
- 2: Poorly grounded - question requires significant external knowledge
- 3: Moderately grounded - question is partially answerable from context
- 4: Well grounded - question is mostly answerable from context
- 5: Perfectly grounded - question is completely answerable from context

Question: {question}

Context: {context}

Please provide your evaluation in the following format:
Analysis: [Your detailed analysis of why the question is or isn't grounded in the context]
Total rating: [Your rating from 1 to 5]
"""

# Question relevance critique prompt template
question_relevance_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how useful this question can be to machine learning developers building NLP applications with the Hugging Face ecosystem.
Give your answer on a scale of 1 to 5, where 1 means that the question is not useful at all, and 5 means that the question is extremely useful.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating, as a text)
Total rating: (your rating, as a number between 1 and 5)

You MUST provide values for 'Evaluation:' and 'Total rating:' in your answer.

Now here is the question.

Question: {question}
Answer::: """

# Question standalone critique prompt template
question_standalone_critique_prompt = """
You will be given a question.
Your task is to provide a 'total rating' representing how context-independent this question is.
Give your answer on a scale of 1 to 5, where 1 means that the question depends on additional information to be understood, and 5 means that the question makes sense by itself.
For instance, if the question refers to a particular setting, like 'in the context' or 'in the document', the rating must be 1.
The questions can contain obscure technical nouns or acronyms like Gradio, Hub, Hugging Face or Space and still be a 5: it must simply be clear to an operator with access to documentation what the question is about.

For instance, "What is the name of the checkpoint from which the ViT model is imported?" should receive a 1, since there is an implicit mention of a context, thus the question is not independent from the context.

Provide your answer as follows:

Answer:::
Evaluation: (your rationale for the rating, as a text)
Total rating: (your rating, as a number between 1 and 5)

You MUST provide values for 'Evaluation:' and 'Total rating:' in your answer.

Now here is the question.

Question: {question}
Answer::: """


class GroundednessMetric(BaseMetric):
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.evaluation_model = "gemini-2.5-pro"
        self.include_reason = True
        
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.evaluation_model,
            temperature=0.3,
        )

    def measure(self, tc: LLMTestCase) -> float:
        """Synchronous version of the metric evaluation."""
        prompt = question_groundedness_critique_prompt.format(
            question=tc.input, 
            context="\n".join(tc.context or [])
        )
        
        try:
           
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            #
            if "Total rating:" in response_text:
                rating_line = response_text.split("Total rating:")[-1].strip()
                
                score_1_5 = int(rating_line.split()[0])
            else:
                
                lines = response_text.split('\n')
                score_1_5 = 3 
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['rating:', 'score:']):
                        try:
                            score_1_5 = int([char for char in line if char.isdigit()][0])
                            break
                        except (IndexError, ValueError):
                            continue
            
            # Convert to 0-1 scale as expected by DeepEval
            self.score = score_1_5 / 5.0
            self.reason = response_text
            self.success = self.score >= self.threshold
            
            return self.score
            
        except Exception as e:
            self.score = 0.0
            self.reason = f"Error during evaluation: {str(e)}"
            self.success = False
            self.error = str(e)
            return self.score

    async def a_measure(self, tc: LLMTestCase):
        """Async version - fallback to synchronous since we don't have async client setup."""
        return self.measure(tc)

    def is_successful(self) -> bool:
        """Check if the metric evaluation was successful."""
        return False if getattr(self, "error", None) else self.success

    @property
    def __name__(self):
        return "Question Groundedness"


class QuestionRelevanceMetric(BaseMetric):
    """DeepEval metric for evaluating question relevance to ML developers building NLP applications."""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.evaluation_model = "gemini-2.5-pro"
        self.include_reason = True
        
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.evaluation_model,
            temperature=0.3,
        )

    def measure(self, tc: LLMTestCase) -> float:
        """Synchronous version of the metric evaluation."""
        prompt = question_relevance_critique_prompt.format(
            question=tc.input
        )
        
        try:
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            
            if "Total rating:" in response_text:
                rating_line = response_text.split("Total rating:")[-1].strip()
                score_1_5 = int(rating_line.split()[0])
            else:
                lines = response_text.split('\n')
                score_1_5 = 3  # Default score
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['rating:', 'score:']):
                        try:
                            score_1_5 = int([char for char in line if char.isdigit()][0])
                            break
                        except (IndexError, ValueError):
                            continue
            
            # Convert to 0-1 scale as expected by DeepEval
            self.score = score_1_5 / 5.0
            self.reason = response_text
            self.success = self.score >= self.threshold
            
            return self.score
            
        except Exception as e:
            self.score = 0.0
            self.reason = f"Error during evaluation: {str(e)}"
            self.success = False
            self.error = str(e)
            return self.score

    async def a_measure(self, tc: LLMTestCase):
        """Async version - fallback to synchronous since we don't have async client setup."""
        return self.measure(tc)

    def is_successful(self) -> bool:
        """Check if the metric evaluation was successful."""
        return False if getattr(self, "error", None) else self.success

    @property
    def __name__(self):
        return "Question Relevance"


class QuestionStandaloneMetric(BaseMetric):
    """DeepEval metric for evaluating question context-independence."""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.evaluation_model = "gemini-2.5-pro"
        self.include_reason = True
        
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.evaluation_model,
            temperature=0.3,
        )

    def measure(self, tc: LLMTestCase) -> float:
        """Synchronous version of the metric evaluation."""
        prompt = question_standalone_critique_prompt.format(
            question=tc.input
        )
        
        try:
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            
            if "Total rating:" in response_text:
                rating_line = response_text.split("Total rating:")[-1].strip()
                
                score_1_5 = int(rating_line.split()[0])
            else:
               
                lines = response_text.split('\n')
                score_1_5 = 3  # Default score
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['rating:', 'score:']):
                        try:
                            score_1_5 = int([char for char in line if char.isdigit()][0])
                            break
                        except (IndexError, ValueError):
                            continue
            
     
            self.score = score_1_5 / 5.0
            self.reason = response_text
            self.success = self.score >= self.threshold
            
            return self.score
            
        except Exception as e:
            self.score = 0.0
            self.reason = f"Error during evaluation: {str(e)}"
            self.success = False
            self.error = str(e)
            return self.score

    async def a_measure(self, tc: LLMTestCase):
        """Async version - fallback to synchronous since we don't have async client setup."""
        return self.measure(tc)

    def is_successful(self) -> bool:
        """Check if the metric evaluation was successful."""
        return False if getattr(self, "error", None) else self.success

    @property
    def __name__(self):
        return "Question Standalone"