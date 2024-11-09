.PHONY: init init-dev format check clean

init:
	@python3 -m venv .venv && \
		. .venv/bin/activate && \
		pip install -r requirements.txt && \
		pip install -e .

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

clean:
	@rm -f llm_tests_output.txt

llm-tests: clean
	@. .venv/bin/activate && \
		./auto_evaluation/llm_tests.sh > llm_tests_output.txt 2>&1
