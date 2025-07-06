# ORAssistant Frontend

## Overview

This is the frontend application for ORAssistant built using Next.js.

## Setup

### Prerequisites

Installation has been tested with:

- Node.js >= `v22.13.0`
- Yarn package manager >= `v1.22.22`

### Installation

Install dependencies:

```bash
yarn install
```

### Development

To run the development server:

```bash
yarn dev

# Format and lint
yarn format
yarn lint
```

## Configuration

1. Create a `.env` file in the root directory
2. Add your hosted backend link:

```
NEXT_PUBLIC_PROXY_ENDPOINT=http://localhost:8000
```

Note:

- You can generate a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
