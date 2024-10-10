FOLDERS=backend frontend

init:
	@for folder in $(FOLDERS); do (cd $$folder && make init && cd ../); done

format: init
	@for folder in $(FOLDERS); do (cd $$folder && make format && cd ../); done

check: format
	@for folder in $(FOLDERS); do (cd $$folder && make check && cd ../); done
	@. ./backend/.venv/bin/activate && \
		pre-commit run --all-files

docker:
	@docker compose up --build --wait
