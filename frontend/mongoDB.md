# MongoDB Feedback Integration Documentation

## Overview

The MongoDB integration provides functionality to store and manage user feedback for the ORAssistant system. It uses a dedicated database called `feedback_db` with a collection for storing feedback records.

## Configuration

Add to your `.env` file:
(Also refer to `.env.example` for more details)

```bash
# atlas cloud
MONGO_DB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net

# local
MONGO_DB_URI=mongodb://localhost:27017
```

Add the correct environment variable based on whether you are using MongoDB Atlas (Cloud) or local deployment.
Refer to the following links for the guides
- MongoDB Atlas [link](https://www.mongodb.com/docs/atlas/getting-started/)
- MongoDB local [link](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-community-with-docker/)

## Database Schema

### Feedback Collection

The `feedback` collection uses JSON Schema validation with the following structure:

```
{
    "question": string,       // The user's question
    "answer": string,        // The AI's response
    "sources": [{            // Array of source-context pairs
        "source": string,    // Source URL/reference
        "context": string    // Context from the source
    }],
    "issue": string,         // Description of the issue/feedback
    "version": string,       // Version of the system
    "timestamp": date,       // When feedback was submitted
    "status": enum          // Status: "new", "processing", "resolved"
}
```

Currently there is only one database schema, but later on the sources field would be encapsulated in another schema for better decoupling

## Usage Example

```python
from utils.mongo_client import submit_feedback

# Submit feedback
submit_feedback(
    question="How do I use OpenROAD?",
    answer="OpenROAD is a tool that...",
    context_sources=[{
        "source": "docs/getting_started.md",
        "context": "OpenROAD installation guide..."
    }],
    issue="Incomplete answer",
    version="1.0.0"
)
```

## Key Functions

1. `get_mongo_db_client()`: Establishes connection to MongoDB

2. `submit_feedback()`: Stores feedback with validation

3. `check_collection_exists()`: Verifies collection presence

4. `create_collection()`: Creates new collection with schema validation

### Error Handling

- Collection creation failures are logged
- Feedback submission errors are caught and reported
- Schema validation ensures data integrity

For more detailed implementation, refer to `frontend/utils/mongo_client.py`.
