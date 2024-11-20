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
		ruff format

check:
	@. .venv/bin/activate && \
		mypy . && \
		ruff check

clean:
	@rm -f llm_tests_output.txt
	@rm -f **/.deepeval-cache.json

llm-tests: clean
	@. .venv/bin/activate && \
		cd auto_evaluation && \
		./llm_tests.sh 2>&1 | tee llm_tests_output.txt
