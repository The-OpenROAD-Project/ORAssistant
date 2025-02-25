FOLDERS=backend frontend evaluation

.PHONY: init
init:
	@for folder in $(FOLDERS); do (cd $$folder && make init && cd ../); done

.PHONY: init-dev
init-dev:
	@for folder in $(FOLDERS); do (cd $$folder && make init-dev && cd ../); done

.PHONY: format
format:
	@for folder in $(FOLDERS); do (cd $$folder && make format && cd ../); done

.PHONY: check
check:
	@for folder in $(FOLDERS); do (cd $$folder && make check && cd ../); done
	@. ./backend/.venv/bin/activate && \
		pre-commit run --all-files

.PHONY: docker-up
docker-up:
	@docker compose up --build --wait

.PHONY: docker-down
docker-down:
	@docker compose down --remove-orphans

.PHONY: changelog
changelog:
	@git log --pretty=format:"%h%x09%an%x09%ad%x09%s" --date=short --since="2024-06-01" > CHANGELOG.md
	@cd .github/workflows && python changelog_report.py
