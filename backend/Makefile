.PHONY: init
init:
	@uv venv .venv && \
		uv sync

.PHONY: init-dev
init-dev:
	@uv venv .venv && \
		uv sync --dev

.PHONY: format
format:
	@uv run ruff format && \
		uv run ruff check --fix

.PHONY: check
check:
	@uv run mypy . && \
		uv run ruff check

.PHONY: build-docs
build-docs:
	@uv run python build_docs.py

.PHONY: test
test:
	@uv run pytest

.PHONY: mcp
mcp:
	@uv run python -m src.openroad_mcp.server.orfs.orfs_server

.PHONY: chat
chat:
	@uv run python -m chatbot
