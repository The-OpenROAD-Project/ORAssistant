FROM python:3.12.3-slim

WORKDIR /ORAssistant-frontend

COPY ./requirements.txt /ORAssistant-frontend/requirements.txt
COPY ./requirements-test.txt /ORAssistant-frontend/requirements-test.txt
COPY ./pyproject.toml /ORAssistant-frontend/pyproject.toml

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -e .

COPY streamlit_app.py .
COPY ./utils ./utils
COPY ./assets ./assets
COPY ../common ./common

CMD ["streamlit", "run", "streamlit_app.py"]
