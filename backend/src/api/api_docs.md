# API Documentation

## Conversations Router

Base URL: `/conversations`

### Conversation API 

#### GET /conversations

List all conversations.

**Query Parameters:**

- `skip`: Number of conversations to skip (default: 0)
- `limit`: Maximum number of conversations to return (default: 100)

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

**Status Codes:**

- 200: Successful response
- 422: Validation error

#### GET /conversations/{id}

Get a specific conversation with all messages.

**Path Parameters:**

- `id`: The unique identifier (UUID) of the conversation

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": [
    {
      "id": 1,
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "string",
      "context_sources": null,
      "tools": null,
      "created_at": "datetime"
    },
    {
      "id": 2,
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "assistant",
      "content": "string",
      "context_sources": {"source": "...", "context": "..."},
      "tools": ["tool_name"],
      "created_at": "datetime"
    }
  ]
}
```

**Status Codes:**

- 200: Successful response
- 404: Conversation not found
- 422: Validation error

#### DELETE /conversations/{id}

Delete a conversation and all its messages.

**Path Parameters:**

- `id`: The unique identifier (UUID) of the conversation to delete

**Response:**

No content (204)

**Status Codes:**

- 204: Conversation deleted successfully
- 404: Conversation not found
- 422: Validation error

### Chat Endpoints

#### POST /conversations/agent-retriever

Get a response from the agent with conversation context and retrieval.

**Request Body:**

```json
{
  "query": "string",
  "conversation_id": "string (optional)",
  "list_sources": "boolean (optional)",
  "list_context": "boolean (optional)"
}
```

**Response:**

```json
{
  "response": "string",
  "context_sources": [
    {
      "context": "string",
      "source": "string"
    }
  ],
  "tools": ["string"]
}
```

**Status Codes:**

- 200: Successful response
- 422: Validation error
- 500: Internal server error

**Parameters:**

- `query`: The user's question or input text
- `conversation_id`: Optional UUID identifier to maintain conversation continuity (auto-generated if not provided)
- `list_sources`: Include source URLs in the response
- `list_context`: Include retrieved context text in the response

#### POST /conversations/agent-retriever/stream

Get a streaming response from the agent.

**Request Body:**

```json
{
  "query": "string",
  "conversation_id": "string (optional)"
}
```

**Response:**

Returns a streaming response with `text/event-stream` media type. The stream includes:

- LLM response chunks as they are generated
- Source URLs at the end of the stream

**Status Codes:**

- 200: Successful streaming response
- 422: Validation error
- 500: Internal server error

 
