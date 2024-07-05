FROM python:3.12.3-slim

RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /ORAssistant-backend

COPY ./requirements.txt /ORAssistant-backend/requirements.txt

RUN pip install --upgrade -r /ORAssistant-backend/requirements.txt

COPY . .

RUN python /ORAssistant-backend/scrape_docs.py 

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

