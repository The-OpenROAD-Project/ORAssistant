FROM python:3.12.3-slim

WORKDIR /ORAssistant-backend

COPY ./requirements.txt /ORAssistant-backend/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /ORAssistant-backend/requirements.txt

COPY . .

RUN python scrape_docs.py 

EXPOSE 8000

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]

