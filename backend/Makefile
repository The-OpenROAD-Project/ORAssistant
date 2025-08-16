.PHONY: init
init:
	@python3 -m venv .venv && \
		. .venv/bin/activate && \
		pip install -r requirements.txt && \
		pip install -e .

.PHONY: init-dev
init-dev: init
	@. .venv/bin/activate && \
		pip install -r requirements-test.txt

.PHONY: format
format:
	@. .venv/bin/activate && \
		ruff format && \
		ruff check --fix

.PHONY: check
check:
	@. .venv/bin/activate && \
		mypy . && \
		ruff check

.PHONY: build-docs
build-docs:
	@. .venv/bin/activate && \
		python build_docs.py

.PHONY: test
test:
	@. .venv/bin/activate && \
		pytest

# For MCP Development
.PHONY: mcp
mcp:
	@. .venv/bin/activate && \
		python -m src.openroad_mcp.server.orfs.orfs_server

.PHONY: chat
chat:
	@. .venv/bin/activate && \
		python -m chatbot
