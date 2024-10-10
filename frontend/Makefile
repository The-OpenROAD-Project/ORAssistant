init:
	@python3 -m venv .venv && \
		. .venv/bin/activate && \
		pip install -r requirements.txt

init-dev: init
	@. .venv/bin/activate && \
		pip install -r requirements-test.txt

format: init-dev
	@. .venv/bin/activate && \
		ruff format

check: init-dev
	@. .venv/bin/activate && \
		ruff check -fix && \
		mypy .
