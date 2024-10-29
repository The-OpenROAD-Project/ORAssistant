FROM python:3.12.3-slim

WORKDIR /ORAssistant-backend

RUN apt-get update && apt-get install -y \
    pandoc git wget curl \
    git-lfs

RUN git lfs install

COPY ./requirements.txt /ORAssistant-backend/requirements.txt
COPY ./requirements-test.txt /ORAssistant-backend/requirements-test.txt
COPY ./pyproject.toml /ORAssistant-backend/pyproject.toml

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -e .

RUN git clone https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset && \
    mkdir -p data && \
    mv ORAssistant_RAG_Dataset/* data/ && \
    rm -rf ORAssistant_RAG_Dataset

COPY . .

RUN python /ORAssistant-backend/src/post_install.py

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
