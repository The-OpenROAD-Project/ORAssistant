# ORAssistant Frontend

## Overview

This is the frontend application for ORAssistant built using Next.js.

There is also a Flask backend that is used to proxy the requests to the Backend API.

## Setup

### Prerequisites

Installation has been tested with these:

- Node.js >= `v22.13.0`
- Yarn package manager >= `v1.22.22`

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
NEXT_PUBLIC_PROXY_ENDPOINT=http://localhost:8000/ui/chat
```
Note:

- You can generate a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- The proxy endpoint is set to `http://localhost:8000/ui/chat` for development purposes.
