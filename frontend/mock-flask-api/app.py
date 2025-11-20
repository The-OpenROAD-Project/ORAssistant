import os
import time
import uuid
import json
import random
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
PORT = int(os.getenv('PORT', 8000))

# --- In-Memory Database ---
# Structure mimics: backend/src/database/models.py
conversations_db = {}

# --- Helpers ---
def get_utc_now():
    return datetime.now(timezone.utc).isoformat()

def generate_fake_context():
    """Mimics the RAG output with OpenROAD specific sources"""
    return {
        "sources": [
            {
                "source": "https://openroad.readthedocs.io/en/latest/main/README.html",
                "context": "OpenROAD is an automated physical design tool..."
            },
            {
                "source": "manpages/man1/global_placement.md",
                "context": "Global placement (gpl) distributes cells across the core..."
            }
        ]
    }

# Validation helpers and error handling

class ValidationError(ValueError):
    """Raised when incoming request bodies are invalid."""


def parse_json_body(required_fields=None, allow_empty=False):
    """
    Parse the JSON body, optionally allowing empty payloads (treated as {}).
    Raises ValidationError if JSON is missing or required fields are absent.
    """
    has_body = request.content_length not in (None, 0)
    if allow_empty and not has_body:
        data = {}
    else:
        data = request.get_json(silent=True)
        if data is None:
            raise ValidationError("Request body must be JSON.")

    if required_fields:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValidationError(f"Missing required field(s): {', '.join(missing)}.")

    return data


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.exception("Unhandled exception: %s", error)
    return jsonify({"error": "Internal server error"}), 500


# --- Routes matching backend/src/api/routers ---

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "ok"})

# --- Helpers Router (backend/src/api/routers/helpers.py) ---
@app.route('/helpers/suggestedQuestions', methods=['POST'])
def suggested_questions():
    """
    Mimics the OpenAI/Gemini call to generate next questions.
    """
    parse_json_body(allow_empty=True)
    return jsonify({
        "suggested_questions": [
            "How do I install OpenROAD flow scripts?",
            "What is the difference between Global and Detailed Routing?",
            "How to fix LVS errors in Sky130?",
            "Explain the CTS (Clock Tree Synthesis) stage."
        ]
    })

# --- Conversations Router (backend/src/api/routers/conversations.py) ---

@app.route('/conversations', methods=['POST'])
def create_conversation():
    data = parse_json_body(allow_empty=True)
    title = data.get('title', "New Conversation")
    if 'title' in data and (not isinstance(title, str) or not title.strip()):
        raise ValidationError("title must be a non-empty string when provided.")

    new_id = str(uuid.uuid4())
    conversations_db[new_id] = {
        "uuid": new_id,
        "title": title,
        "created_at": get_utc_now(),
        "updated_at": get_utc_now(),
        "messages": []
    }
    return jsonify(conversations_db[new_id]), 201

@app.route('/conversations', methods=['GET'])
def list_conversations():
    # Sort by updated_at desc (mimicking crud.get_all_conversations)
    conv_list = list(conversations_db.values())
    conv_list.sort(key=lambda x: x['updated_at'], reverse=True)
    
    # The list response in backend/src/api/models/response_model.py excludes messages
    response_list = []
    for c in conv_list:
        response_list.append({
            "uuid": c['uuid'],
            "title": c['title'],
            "created_at": c['created_at'],
            "updated_at": c['updated_at']
        })
    return jsonify(response_list)

@app.route('/conversations/<uuid_str>', methods=['GET'])
def get_conversation(uuid_str):
    if uuid_str not in conversations_db:
        return jsonify({"detail": "Conversation not found"}), 404
    return jsonify(conversations_db[uuid_str])

@app.route('/conversations/<uuid_str>', methods=['DELETE'])
def delete_conversation(uuid_str):
    if uuid_str in conversations_db:
        del conversations_db[uuid_str]
        return Response(status=204)
    return jsonify({"detail": "Conversation not found"}), 404

@app.route('/conversations/agent-retriever', methods=['POST'])
def agent_retriever():
    """
    Simulates the non-streaming RAG agent.
    """
    data = parse_json_body(required_fields=['query'])
    user_query = data['query']
    if not isinstance(user_query, str) or not user_query.strip():
        raise ValidationError("query must be a non-empty string.")

    conv_id = data.get('conversation_uuid')
    if conv_id and not isinstance(conv_id, str):
        raise ValidationError("conversation_uuid must be a string.")

    # 1. Handle Conversation Creation if ID is missing
    if not conv_id:
        conv_id = str(uuid.uuid4())
        title = user_query[:100] if user_query else "New Conversation"
        conversations_db[conv_id] = {
            "uuid": conv_id,
            "title": title,
            "created_at": get_utc_now(),
            "updated_at": get_utc_now(),
            "messages": []
        }
    
    # 2. Save User Message
    conversations_db[conv_id]['messages'].append({
        "uuid": str(uuid.uuid4()),
        "conversation_uuid": conv_id,
        "role": "user",
        "content": user_query,
        "created_at": get_utc_now()
    })

    # Simulate Latency
    time.sleep(1)

    # 3. Generate Fake Answer
    fake_answer = f"This is a **mock backend** response to: '{user_query}'.\n\nI am simulating the `RetrieverGraph`. Here is some information about OpenROAD:\n\n- It is an open-source flow.\n- It uses yosys, openSTA, etc."
    context_sources = generate_fake_context()
    tools_used = ["retrieve_general"]

    # 4. Save Assistant Message
    conversations_db[conv_id]['messages'].append({
        "uuid": str(uuid.uuid4()),
        "conversation_uuid": conv_id,
        "role": "assistant",
        "content": fake_answer,
        "context_sources": context_sources,
        "tools": tools_used,
        "created_at": get_utc_now()
    })
    
    conversations_db[conv_id]['updated_at'] = get_utc_now()

    # 5. Return ChatResponse model
    return jsonify({
        "response": fake_answer,
        "context_sources": [
            {"source": s["source"], "context": s["context"]} 
            for s in context_sources["sources"]
        ],
        "tools": tools_used
    })

@app.route('/conversations/agent-retriever/stream', methods=['POST'])
def agent_retriever_stream():
    """
    Simulates the Streaming Endpoint.
    Matches backend logic: Yields "Sources: ..." then text chunks.
    """
    data = parse_json_body(required_fields=['query'])
    user_query = data['query']
    if not isinstance(user_query, str) or not user_query.strip():
        raise ValidationError("query must be a non-empty string.")

    conv_id = data.get('conversation_uuid')
    if conv_id and not isinstance(conv_id, str):
        raise ValidationError("conversation_uuid must be a string.")

    # Handle logic to find/create conversation (same as above)
    if not conv_id or conv_id not in conversations_db:
        conv_id = str(uuid.uuid4())
        title = user_query[:100] if user_query else "New Conversation"
        conversations_db[conv_id] = {
            "uuid": conv_id,
            "title": title,
            "created_at": get_utc_now(),
            "updated_at": get_utc_now(),
            "messages": []
        }

    # Save User Message
    conversations_db[conv_id]['messages'].append({
        "uuid": str(uuid.uuid4()),
        "conversation_uuid": conv_id,
        "role": "user",
        "content": user_query,
        "created_at": get_utc_now()
    })

    def generate():
        # 1. Simulate "Thinking"
        time.sleep(0.5)

        # 2. Send Sources first (Mimicking backend behavior)
        sources = ["https://openroad.readthedocs.io/en/latest/", "manpages/ant.md"]
        yield f"Sources: {', '.join(sources)}\n\n"
        
        time.sleep(0.5)

        # 3. Stream Text Chunks
        full_response = f"I am streaming a response regarding **{user_query}**.\n\n"
        yield full_response
        
        words = "OpenROAD is a fast, autonomous, open-source tool flow for digital layout generation. It covers synthesis to GDSII.".split()
        
        buffer = ""
        for word in words:
            chunk = word + " "
            buffer += chunk
            yield chunk
            time.sleep(0.1) # Simulate token generation speed

        # 4. Save the completed message to DB (for history)
        conversations_db[conv_id]['messages'].append({
            "uuid": str(uuid.uuid4()),
            "conversation_uuid": conv_id,
            "role": "assistant",
            "content": full_response + buffer,
            "context_sources": {"sources": [{"source": s, "context": ""} for s in sources]},
            "tools": ["retrieve_general"],
            "created_at": get_utc_now()
        })
        conversations_db[conv_id]['updated_at'] = get_utc_now()

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    print(f"🚀 Fake OpenROAD Backend running on http://localhost:{PORT}")
    print("   - Simulating Postgres, VectorDB, and LLM")
    app.run(host='0.0.0.0', port=PORT, debug=app.config['DEBUG'])