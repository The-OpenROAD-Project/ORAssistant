init:
	@python3 -m venv .venv && \
		. .venv/bin/activate && \
		pip install -r requirements.txt

init-dev: init
	@. .venv/bin/activate && \
		pip install -r requirements-test.txt

format:
	@. .venv/bin/activate && \
		ruff format && \
		mypy .

check:
	@. .venv/bin/activate && \
		ruff check --fix
