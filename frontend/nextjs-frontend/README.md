# ORAssistant Frontend

## Overview

This is the frontend application for ORAssistant built using Next.js.

## Setup

### Prerequisites

Installation has been tested with:

- Node.js >= `v22.13.0`
- Corepack, which runs the Yarn release pinned in `package.json`. Node.js 24
  includes it; on Node.js 25 and later, run `npm install -g corepack`.

### Installation

Install dependencies:

```bash
corepack enable
yarn install
```

Yarn does not run dependency install scripts (`enableScripts: false` in
`.yarnrc.yml`). If a new dependency needs its script, add it under
`dependenciesMeta` in `package.json` with `built: true`.

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
