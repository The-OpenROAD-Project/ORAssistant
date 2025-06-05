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
		ruff format

.PHONY: check
check:
	@. .venv/bin/activate && \
		mypy . && \
		ruff check

.PHONY: clean
clean:
	@rm -f llm_tests_output.txt
	@rm -f **/.deepeval-cache.json

.PHONY: llm-tests
llm-tests: clean
	@bash -c '\
		. .venv/bin/activate && \
		cd auto_evaluation && \
		./llm_tests.sh 2>&1 | tee llm_tests_output.txt; \
		exit $${PIPESTATUS[0]}'
