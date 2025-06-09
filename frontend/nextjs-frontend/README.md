# ORAssistant Frontend

## Overview

This is the frontend application for ORAssistant built using Next.js.

There is also a Flask backend that is used to proxy the requests to the Backend API.

## Setup

### Prerequisites

Installation has been tested with these:

- Node.js >= `v22.13.0`
- Yarn package manager >= `v1.22.22`
- Python >= `3.10`

### Installation

1. Clone the repository

The following steps should be done in the `nextjs-frontend` directory.

2. Install dependencies:

```bash
yarn install
```

**Note**: This is better done in a virtual environment. For more information see the [Python Installation Guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/).

### Development

To run the development server:

```bash
yarn dev
```

## Configuration

1. Create a `.env` file in the root directory
2. Add your hosted backend link:

```
BACKEND_URL=backend_api_url
GEMINI_API_KEY=api_key // used for suggested question feature
NEXT_PUBLIC_PROXY_ENDPOINT=http://localhost:3001/api/chat
```

**Note**: the backend url will depend on the type of backend you are using. For example, if you are using the mock backend, the url will be `http://localhost:8000/chains/mock`.

## API Proxy Server

This project uses a Flask-based API proxy server (`apiproxy.py`) as an intermediary between the Next.js frontend and the backend API.

### Why We Use a Proxy Server

1. **CORS Mitigation**: Avoids cross-origin resource sharing issues that might occur when making direct requests from the browser to the backend.
2. **Environment Flexibility**: Allows easy switching between different backend environments (development, production, or mock testing) by changing a single environment variable.
3. **Request/Response Logging**: Provides helpful logging for debugging API communication issues.

Note:

- You can generate a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- The proxy endpoint is set to `http://localhost:3001/api/chat` for development purposes.
