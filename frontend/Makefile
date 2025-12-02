.PHONY: init
init:
	@uv venv .venv && \
		uv sync

.PHONY: init-dev
init-dev:
	@uv venv .venv && \
		uv sync --extra test

.PHONY: format
format:
	@uv run ruff format && \
		uv run ruff check --fix

.PHONY: check
check:
	@uv run mypy . && \
		uv run ruff check
