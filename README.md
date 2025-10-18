# ORAssistant

[![ORAssistant CI](https://github.com/The-OpenROAD-Project/ORAssistant/actions/workflows/ci.yaml/badge.svg)](https://github.com/The-OpenROAD-Project/ORAssistant/actions/workflows/ci.yaml)

## Introduction

The OpenROAD chat assistant aims to provide easy and quick access to information regarding tools, responses to questions and commonly occurring problems in OpenROAD and its native flow OpenROAD-flow-scripts.

The current architecture uses certain retrieval techniques on OpenROAD documentation and other online data sources. We aim to continuously improve the architecture and the associated the dataset to improve accuracy, coverage and robustness.

## Use Cases

- **Installation and Troubleshooting Assistance:** The chatbot will provide users with quick and accurate solutions to common installation issues and troubleshooting steps.
- **Easy Access to Existing Resources:** The chatbot will be able to summarize relevant information from OpenROAD documentation, user guides, and online resources to provide concise and actionable answers to user queries.

## Components

We have divided our app into three components, each of which can be hosted on a separate machine for scalability.

- Backend: Generates the necessary chat endpoints for users to communicate with.
- Frontend: We use Streamlit to communicate with a chat endpoint, providing a user-friendly chat interface.
- Evaluation: Besides the vanilla chat interface, we also have a human evaluation interface for research and development.

## Setup

This setup involves the setting of both the frontend and backend components. We shall begin with backend:

### Backend Setup

#### Option 1 - Docker

Ensure you have `docker` and `docker-compose` installed in your system.

**Step 1**: Clone the repository:

```bash
git clone https://github.com/The-OpenROAD-Project/ORAssistant.git
```

**Step 2**: Copy the `.env.example` file, and update your `.env` file with the appropriate API keys.

Modify the Docker `HEALTHCHECK_` variables based on the hardware requirements.
If you have a resource-constrained PC, try increasing `HEALTHCHECK_START_PERIOD` to a value large
enough before healthcheck begins.
For more information, please refer to this [link](https://docs.docker.com/reference/compose-file/services/#healthcheck)


Set the model by updating your `.env` file:
```bash
cd backend
cp .env.example .env
```

**Step 3**: Start and stop the docker containers by running the following command:

```bash
make docker-up
make docker-down
```

#### Option 2 - Local Install

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (for managing Python, virtual environments, and dependencies)
- `wget`
- `pandoc`
- `git`

**Step 1**: Install the required dependencies.

```bash
uv sync
```

**Step 2**: Copy the `.env.example` file, and update your `.env` file with the appropriate API keys.

```bash
cd backend
cp .env.example .env
```

**Step 3**: For populating the `data` folder with OR/ORFS docs, OpenSTA docs and Yosys docs, run:

```bash
python build_docs.py

# Alternatively, pull the latest docs
mkdir data
huggingface-cli download The-OpenROAD-Project/ORAssistant_RAG_Dataset --repo-type dataset --local-dir data/
```

**Step 4**: To run the server, run:

```bash
python main.py
```

**Optionally**: To interact with the chatbot in your terminal, run:

```bash
python chatbot.py
```

The backend will then be hosted at [http://0.0.0.0:8000](http://0.0.0.0:8000).

Open [http://0.0.0.0:8000/docs](http://0.0.0.0:8000/docs) for the API docs.

### Frontend Setup

**Note**: Please refer to the frontend [README](./frontend/README.md) for more detailed instructions.

- **Step 1**: Set up the `.env` as per the instructions in the frontend [README](./frontend/README.md). Get the [Google Sheet API Key](https://developers.google.com/sheets/api/guides/concepts)

```bash
cd frontend
cp .env.example .env
```

- **Step 2**: Install the necessary requirements. You are encouraged to use a virtual environment for this.

```bash
pip install -r requirements.txt
```

- **Step 3**: Run streamlit application

```bash
streamlit run streamlit_app.py
```

## Architecture Overview

OpenROAD documentation, OpenROAD-flow-scripts documentation, manpages and OpenSTA documentation is chunked and embedded into FAISS Vector Databases.

Documents are first retrieved from the vectorstore using a hybrid retriever, combining vector and semantic search methods. These retrieved documents undergo re-ranking using a cross-encoder re-ranker model.

```mermaid
flowchart LR
    id0([Query]) --> id1

    id1([Vectorstore]) --- id2([Semantic Retriever])
    id1([Vectorstore]) --- id3([MMR Retriever])
    id1([Vectorstore]) --- id4([BM25 Retriever])

    id2([Semantic Retriever]) -- Retrieved Docs ---> id5([Reranking])
    id3([MMR Retriever]) -- Retrieved Docs ---> id5([Reranking])
    id4([BM25 Retriever]) -- Retrieved Docs ---> id5([Reranking])

    id5([Reranking]) ---> id6(top-n docs)

```

Depending on the input query, each query can be forwarded to any one of the following retrievers,

1. General OR/ORFS information
2. OR tools and commands
3. OR/ORFS installation
4. OR Error Messages
5. OpenSTA docs
6. Yosys docs
7. Klayout docs

The retrievers act as separate tools and can be accessed by the LLM's tool-calling capabilities.

The `langgraph` framework has been used to make effective use of the multiple retriever tools. Upon receiving a query, a routing LLM call classifies the query and forwards it to the corresponding retriever tool. Relevant documents are the queried from the vectorstore by the tool and sent to the LLM for response generation.

```mermaid
graph TD
    __start__ --> router_agent
    router_agent -.-> retrieve_general
    router_agent -.-> retrieve_cmds
    router_agent -.-> retrieve_install
    router_agent -.-> retrieve_errinfo
    router_agent -.-> retrieve_opensta
    router_agent -.-> retrieve_yosys
    router_agent -.-> retrieve_klayout
    retrieve_general --> generate
    retrieve_cmds --> generate
    retrieve_install --> generate
    retrieve_errinfo --> generate
    retrieve_opensta --> generate
    retrieve_yosys --> generate
    retrieve_klayout --> generate
    generate --> __end__
```

## Dataset overview

The RAG dataset used in this project can be found [here](https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset).

To modify the dataset, please refer to [build_docs.py](./backend/build_docs.py)

## Tests

```
make format
make check
```

## Acknowledgements

This work is completed as part of the Google Summer of Code 2024 project under the
[UCSC Open-Source Program Office](https://ucsc-ospo.github.io/osre24/).
Please see their contributions at this [link](https://github.com/The-OpenROAD-Project/ORAssistant/wiki/Google-Summer-of-Code-2024).

## Citing this work

**2024-10-27**: Our work has been accepted to [Workshop on Open-Source EDA Technology 2024](https://woset-workshop.github.io/). Kudos to our talented contributors Palaniappan R and Aviral Kaintura (contributed equally)!

If you use this software in any published work, we would appreciate a citation! Please use the following reference:

```
@article{kaintura2024orassistant,
  title={ORAssistant: A Custom RAG-based Conversational Assistant for OpenROAD},
  author={Kaintura, Aviral and R, Palaniappan and Luar, Shui Song and Almeida, Indira Iyer},
  journal={arXiv preprint arXiv:2410.03845},
  year={2024}
}
```

```
@misc{orassistant2024,
  author = {Kaintura, Aviral and R, Palaniappan and Luar, Shui Song and Iyer, Indira},
  title = {ORAssistant Repository},
  year = {2024},
  url = {https://github.com/The-OpenROAD-Project/ORAssistant},
  note = {Accessed: 20xx-xx-xx}
}
```
