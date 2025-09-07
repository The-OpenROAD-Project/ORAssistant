# Backend For ORAssistant

This folder contains the backend code for the ORAssistant. Follow the instructions below to set up the environment and run the backend.

## Preparing the Environment Variables

To configure the application, you'll need to set up the environment variables in your `.env` file:

The given command would copy the template for environment variables to a local `.env` file 


```
cp .env.example .env
```


### Setting Up Google API Key and Credentials Variables

There are 2 variables that needs to be set up

- `GOOGLE_API_KEY`

This key is used to access the various google cloud functions.
  - Go to [Google Cloud Console](https://console.cloud.google.com/)
  - Create new project or select existing one
  - Enable required APIs:
       - Google Gemini API
       - Vertex AI API
  - Go to APIs & Services > Credentials
  - Click "Create Credentials" > "API Key"
  - Copy the generated key and it to the `.env` file
  
- `GOOGLE_APPLICATION_CREDENTIALS`
  Since most of the GCP functions / services would be used by our app, we need to have a special credential that would allow `ORAssistant`'s access to the GCP
    Steps to set up Service Account Credentials:
  - In Google Cloud Console, go to IAM & Admin > Service Accounts
  - Click "Create Service Account"
  Fill in service account details
  -  Grant required roles:
       - Vertex AI User
       - Vertex AI Service Agent
  - Create key (JSON format)
  - Download JSON file
  - Store securely and add path to .env:
       `GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json`

**NOTE**: The user might need billing to be set up on google cloud account and make sure to name the file as `credentials.json`  as this would be ignored by `.git` and wouldn't be exposed on Github

### Running ORAssistant with a Local Ollama Model

ORAssistant supports running locally hosted Ollama models for inference. Follow these steps to set it up:

#### 1. Install Ollama  
- Visit [Ollama's installation page](https://ollama.com/download) and follow the installation instructions for your system.

#### 2. Configure ORAssistant to Use Ollama  
- In your `.env` file, set:  
  ```bash
  LLM_MODEL="ollama"
  OLLAMA_MODEL="<model_name>"

Ensure Ollama is running locally before starting ORAssistant. Make sure the model weights are available by downloading them first with `ollama pull <model_name>`.

To take advantage of GPU resources when running ORAssistant in a Docker container, use `ollama serve` on local machine.

### Setting Up LangChain Variables

There are 4 variables that needs to be set up

- `LANGCHAIN_TRACING_V2` 
  
  This is used to enable LangChain's debugging and monitoring features,
  can be set to either `true` or `false`

- `LANGCHAIN_ENDPOINT`
  
  The URL endpoint for LangSmith (LangChain's monitoring platform). 
  Default value should be `https://api.smith.langchain.com` for cloud-hosted LangSmith.
  Used to send trace data, metrics, and debugging information from your LangChain applications.

- `LANGCHAIN_API_KEY`
  
    API key required to authenticate with LangSmith platform.
  - Get your key from: https://smith.langchain.com/
  - Create account if you don't have one
  - Navigate to Settings > API Keys
  - Create new API key
  - Format: starts with `lsv2_` followed by a unique string
  
- `LANGCHAIN_PROJECT`
    
    Project identifier in LangSmith to organize and track your traces.
  - Create new project in LangSmith dashboard
  - Use the project name or ID provided
  - Example: "my-rag-project"
  - Helps organize different applications/environments
  - Multiple apps can share same project
  

### Setting Up Huggingface User Access Token

To set up the `HF_TOKEN` variable in `.env` file , go through the following instructions:

- Go the official website for [Huggingface](https://huggingface.co/) and either Login or Sign up.
- On the main page click on user access token
- Click on create access token
- Provide only Read Instruction for the token and Click on Generate Token
  
  


Provide the value for `HF_TOKEN` with the token that is generated

## Running the Application

To use that chatbot in a text-based in your terminal, use the `chatbot.py` script:
```python
uv run chatbot.py
```

### Install Required Packages

Install dependencies defined in `pyproject.toml` with:

```bash
uv sync
```

### Docker Command

If you want to run an isolated container for backend, you can use the following command 

```bash
docker build -t (image_name) .
```

Make sure you are in the backend folder before running the above command.

**NOTE**: The project does support a `docker-compose` file that would run all of the containers together

### MCP Commands
OpenROAD's MCP server is a wrapper around the OpenROAD-flow-scripts. It utilizes the Streamable HTTP transport so it must be launched as a separate process. Run with `python orfs_server.py`

Currently tested with running `python chatbot.py` in another process.

Note: mcp breaks support for llms without toolchain i.e. json parsing
