FOLDERS=backend frontend

init:
	@for folder in $(FOLDERS); do (cd $$folder && make init && cd ../); done

init-dev:
	@for folder in $(FOLDERS); do (cd $$folder && make init-dev && cd ../); done

format:
	@for folder in $(FOLDERS); do (cd $$folder && make format && cd ../); done

check:
	@for folder in $(FOLDERS); do (cd $$folder && make check && cd ../); done
	@. ./backend/.venv/bin/activate && \
		pre-commit run --files backend/* && \
		pre-commit run --files frontend/*

docker:
	@docker compose up --build --wait
