.PHONY: lock
lock:
	@uv lock

.PHONY: init
init:
	@uv sync

.PHONY: init-dev
init-dev:
	@uv sync --extra test

.PHONY: format
format:
	@uv run ruff format

.PHONY: check
check:
	@uv run mypy . && \
		uv run ruff check && \
		uv run python -m unittest tests/test_dependency_contracts.py tests/test_llm_tests_script.py

.PHONY: clean
clean:
	@rm -f llm_tests_output.txt
	@rm -f **/.deepeval-cache.json

.PHONY: llm-tests
llm-tests: clean
	@bash -c '\
		cd auto_evaluation && \
		uv run ./llm_tests.sh 2>&1 | tee llm_tests_output.txt; \
		exit $${PIPESTATUS[0]}'
