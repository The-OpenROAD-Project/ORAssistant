.PHONY: init init-dev format check

FOLDERS=backend frontend evaluation

init:
	@for folder in $(FOLDERS); do (cd $$folder && make init && cd ../); done

init-dev:
	@for folder in $(FOLDERS); do (cd $$folder && make init-dev && cd ../); done

format:
	@for folder in $(FOLDERS); do (cd $$folder && make format && cd ../); done

check:
	@for folder in $(FOLDERS); do (cd $$folder && make check && cd ../); done
	@. ./backend/.venv/bin/activate && \
		pre-commit run --all-files

docker-up:
	@docker compose up --build --wait

docker-down:
	@docker compose down --remove-orphans

changelog:
	@git log --pretty=format:"%h%x09%an%x09%ad%x09%s" --date=short --since="2024-06-01" > CHANGELOG.md
	@cd .github/workflows && python changelog_report.py
