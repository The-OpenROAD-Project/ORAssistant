FROM python:3.12.3-slim

WORKDIR /ORAssistant-backend

COPY ./requirements.txt /ORAssistant-backend/requirements.txt

RUN pip install --upgrade -r /ORAssistant-backend/requirements.txt

COPY . .

# Prereqs
RUN apt-get update && apt-get install -y make git wget

RUN python /ORAssistant-backend/build_docs.py

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
