# AGENTS.md

ORAssistant answers questions about OpenROAD and OpenROAD-flow-scripts with a
RAG pipeline. `backend/` serves the API, `frontend/` is the UI, and
`evaluation/` sends the question dataset to the backend and scores the answers.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first commit. It owns the
check commands, the sign-off, and the pull request rules.

## Work in one project at a time

Each directory with a `pyproject.toml` is a separate uv project with its own
`uv.lock`. Run `make` targets in the directory of the project you change.
After a dependency change, run `make lock` there and commit the `uv.lock`
with it.

## Tests

- Backend tests run in parallel (`pytest -n auto`). Keep each test on its own
  `tmp_path`, with no shared files or ports.
- Backend tests read `backend/.env`. Copy `backend/.env.test` to `.env` first,
  as CI does.
- `evaluation/` has two test sets: `unittest` files in `evaluation/tests/` and
  pytest files in `evaluation/auto_evaluation/tests/`. `make check` runs both.
- `backend/tests/test_ci_secret_workflow.py` tests the workflows in
  `.github/workflows/`. Update it in the same change as a workflow.

## Workflows

- Pin each action to a full commit SHA, with the version in a comment:
  `uses: actions/checkout@<sha>  # v7.0.1`.
- `ci-secret.yaml` runs the paid LLM evaluation on self-hosted runners. A push
  to `master` that matches its `push.paths` filter starts it. A maintainer
  decides when to run it on a pull request.
- `HF_RAG_REVISION` in `ci-secret.yaml` pins the RAG corpus on Hugging Face.
  Set it only to the commit in the job summary of a successful `upload.yml`
  run.
