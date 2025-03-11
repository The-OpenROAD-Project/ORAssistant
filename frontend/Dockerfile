FROM python:3.12.3-slim

WORKDIR /ORAssistant-frontend

COPY frontend/requirements.txt /ORAssistant-frontend/requirements.txt
COPY frontend/requirements-test.txt /ORAssistant-frontend/requirements-test.txt
COPY frontend/pyproject.toml /ORAssistant-frontend/pyproject.toml

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -e .

COPY frontend/streamlit_app.py .
COPY frontend/utils ./utils
COPY frontend/assets ./assets
COPY common ./common

CMD ["streamlit", "run", "streamlit_app.py"]
