FROM python:3.12.3-slim

WORKDIR /ORAssistant-backend

COPY ./requirements.txt /ORAssistant-backend/requirements.txt

RUN pip install --upgrade -r /ORAssistant-backend/requirements.txt

COPY . .

RUN apt-get update && apt-get install -y git

RUN git clone https://huggingface.co/datasets/The-OpenROAD-Project/ORAssistant_RAG_Dataset && \
    rm -rf data && \
    mkdir -p data && \
    mv ORAssistant_RAG_Dataset/* data/ && \
    rm -rf ORAssistant_RAG_Dataset

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

