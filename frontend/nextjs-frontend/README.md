# ORAssistant Frontend

This is the frontend application for ORAssistant built using Next.js.

## Setup

### Prerequisites
- Node.js
- Yarn package manager

### Installation

1. Clone the repository
2. Install dependencies:
```bash
yarn install
```

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
```

### Suggested Questions Feature

For the suggested questions feature that uses Gemini 1.5:

1. Navigate to `orassistant-chat/.env`
2. Add the following environment variables:
```
GEMINI_API_KEY=api_key
NEXT_PUBLIC_PROXY_ENDPOINT=localhost:3001/api/chat
```

Note:
- You can generate a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- The proxy endpoint is set to localhost:3001 for development


