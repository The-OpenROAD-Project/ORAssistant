# OR-Assistant

## Setup

### Option 1 - Docker

Ensure you have `docker` and `docker-compose` installed in your system.

- **Step 1**: Clone the repository:
```bash
  git clone https://github.com/The-OpenROAD-Project/ORAssistant.git
``` 
- **Step 2**: Copy the `.env.example` file, and update your `.env` file with the appropriate API keys. Get the [Google Gemini API Key](https://ai.google.dev) and add it to your env file, add other env vars as required.
```bash
  cd backend
  cp .env.example .env
```

- **Step 3**: Start the server by running the following command,
```bash
  docker compose up
```

### Option 2 - Local Install

- Follow **Step 1** and **Step 2** as mentioned above.
- **Step 3**: To scrape OR/ORFS docs and populate the `data` folder, run
```bash
  python src/tools/scrape_userguide.py
```
- **Step 4**: To run the server,
```bash
  cd backend
  python main.py
```

The backend will then be hosted at [http://0.0.0.0:8000](http://0.0.0.0:8000). 

Open [http://0.0.0.0:8000/docs](http://0.0.0.0:8000/docs) for the API docs.