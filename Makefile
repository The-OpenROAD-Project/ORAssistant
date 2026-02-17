FOLDERS=backend frontend evaluation
GOOGLE_SECRET_JSON?=$(HOME)/secret.json

.PHONY: init
init:
	@pids=""; \
	 for folder in $(FOLDERS); do (cd $$folder && make init) & pids="$$pids $$!"; done; \
	 for pid in $$pids; do wait $$pid || exit 1; done

.PHONY: init-dev
init-dev:
	@pids=""; \
	 for folder in $(FOLDERS); do (cd $$folder && make init-dev) & pids="$$pids $$!"; done; \
	 for pid in $$pids; do wait $$pid || exit 1; done

.PHONY: format
format:
	@pids=""; \
	 for folder in $(FOLDERS); do (cd $$folder && make format) & pids="$$pids $$!"; done; \
	 for pid in $$pids; do wait $$pid || exit 1; done

.PHONY: check
check:
	@pids=""; \
	 for folder in $(FOLDERS); do (cd $$folder && make check) & pids="$$pids $$!"; done; \
	 for pid in $$pids; do wait $$pid || exit 1; done
	@. ./backend/.venv/bin/activate && \
		pre-commit run --all-files

.PHONY: docker-up
docker-up:
	@docker compose -f docker-compose.yml up --build --wait

.PHONY: docker-down
docker-down:
	@docker compose -f docker-compose.yml down --remove-orphans

.PHONY: docker-dev
docker-dev:
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build --wait

# --- Development Commands ---
.PHONY: seed-credentials
seed-credentials:
	@cp $(GOOGLE_SECRET_JSON) backend/src
	@cp $(GOOGLE_SECRET_JSON) evaluation/auto_evaluation/src

.PHONY: changelog
changelog:
	@git log --pretty=format:"%h%x09%an%x09%ad%x09%s" --date=short --since="2024-06-01" > CHANGELOG.md
	@cd .github/workflows && python changelog_report.py
