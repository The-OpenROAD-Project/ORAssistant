from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

# HARDCODED collection names
feedback_collection_name = "feedback"
source_collection_name = "source"

def get_mongo_db_client() -> Database:
    """
    Get the MongoDB client.

    Returns:
    - DatabaseClient: The Database client.

    Note:
    MongoDB doesn't create a collection or a database until it gets content, so no need to check if the data already exists or not.
    """

    uri = os.getenv("MONGO_DB_URI")
    client = MongoClient(uri)
    # this is the database that is returned by the client
    return client["feedback_db"]

def submit_feedback(
    question: str,
    answer: str,
    context_sources: list[dict[str, str]],
    issue: str,
    version: str,
):
    """
    Submit feedback Record to the MongoDB database.

    Args:
    - question (str): The question for which feedback is being submitted.
    - answer (str): The generated answer to the question.
    - context_sources (list[dict[str, str]]): List of source-context pairs.
    - issue (str): Details about the issue.
    - version (str): Version information.

    Returns:
    - None
    """

    feedback_db_client = get_mongo_db_client()

    try:
        if not check_collection_exists(feedback_collection_name,feedback_db_client,):
            create_collection(feedback_collection_name,feedback_db_client,                validator={
                    '$jsonSchema': {
                        'bsonType': 'object',
                        'required': ['question', 'answer', 'sources', 'issue', 'version', 'timestamp'],
                        'properties': {
                            'question': 
                            {
                                'bsonType': 'string',
                                'description': 'must be a string and is required'
                            },
                            'answer': 
                            {
                                'bsonType': 'string',
                                'description': 'must be a string and is required'
                            },
                            'sources': {
                                'bsonType': 'array',
                                'items': {
                                    'bsonType': 'object',
                                    'required': ['source', 'context'],
                                    'properties': {
                                        'source': {
                                            'bsonType': 'string',
                                            'description': 'must be a string and is required'
                                        },
                                        'context': {
                                            'bsonType': 'string',
                                            'description': 'must be a string and is required'
                                        }
                                    }
                                },
                                'description': 'must be an array of source-context pairs and is required'
                            },
                            'issue': 
                            {
                                'bsonType': 'string',
                                'description': 'must be a string and is required'
                            },
                            'version': 
                            {
                                'bsonType': 'string',
                                'description': 'must be a string and is required'
                            },
                            'timestamp': 
                            {
                                'bsonType': 'date',
                                'description': 'must be a date and is required'
                            },
                            'status': 
                            {
                                'enum': ['new', 'processing', 'resolved'],
                                'description': 'can only be one of the enum values'
                            }
                        }
                    }
                })

        feedback_db_client[feedback_collection_name].insert_one({
            'question': question,
            'answer': answer,
            'sources': context_sources,
            'issue': issue,
            'version': version,
            'timestamp': datetime.now(),
            'status': 'new'
        })

        print("Feedback submitted successfully") 
        return True
    except Exception as e:
        print(f"Failed to submit feedback: {e}")
        return None
    
def check_collection_exists(collection_name:str,client_database:Database)->bool:
    """
    Check if the collection exists in the database.

    Args:
    - collection_name (str): The name of the collection to check.
    - client_database (Database): The database to check.

    Returns:
    - None
    """
    return collection_name in client_database.list_collection_names()

def create_collection(collection_name:str,client_database:Database,validator:object)->None:
    """
    Create a collection in the database.

    Args:
    - collection_name (str): The name of the collection to create.
    - client_database (Database): The database to create the collection in.

    Returns:
    - None
    """
    try:
        client_database.create_collection(collection_name,validator=validator)
        print("Collection created successfully")
    except Exception as e:
        print(f"Failed to create collection: {e}")
        return None

if __name__ == "__main__":
    submit_feedback()
