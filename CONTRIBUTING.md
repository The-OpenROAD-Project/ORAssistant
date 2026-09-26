# Contributing to ORAssistant

Thank you for your help. This file tells you how to set up, check, and submit
a change. By contributing, you agree that your work is licensed under the
project's [GPL-3.0 license](LICENSE).

Report bugs and ask for features in
[GitHub issues](https://github.com/The-OpenROAD-Project/ORAssistant/issues).

## Set up

The repository has four Python projects, each with its own `uv.lock`:

- `backend/`: the FastAPI server and the RAG pipeline. It needs Python 3.13.
- `frontend/`: the Streamlit UI. The Next.js UI is in `frontend/nextjs-frontend/`.
- `evaluation/`: the LLM evaluation (auto and human).
- `frontend/mock-flask-api/`: a mock backend API to test the UI.

Install [uv](https://docs.astral.sh/uv/). Then install the development
dependencies of the first three projects from the repository root:

```
make init-dev
```

For the mock API, run `make init` in `frontend/mock-flask-api/`.

To run the application, follow [Setup](README.md#setup) in the README and the
environment variables in [backend/README.md](backend/README.md).

## Check your change

Run these from the repository root before you open a pull request:

```
make format
make check
```

`make check` runs mypy and ruff in each project, the evaluation tests, and the
[pre-commit](https://pre-commit.com/) hooks. To check only one project, run
`make check` in its directory.

Run the backend tests from `backend/`:

```
cp .env.test .env
make test
```

`.env.test` holds placeholder values, so the tests need no credentials.

For the Next.js UI, run `yarn lint` and `yarn format` in
`frontend/nextjs-frontend/`. CI does not check this project.

When you change a dependency, update the lock file with `make lock` in that
project's directory.

## Commit

Sign off each commit to certify the
[Developer Certificate of Origin](https://developercertificate.org/):

```
git commit -s
```

The `DCO` check fails on a pull request that has a commit without a
`Signed-off-by` line.

## Open a pull request

- Keep one concern in each pull request.
- Write the title as a [Conventional Commit](https://www.conventionalcommits.org/)
  subject, for example `fix(backend): return one context source per chunk`.
  The project merges by squash, so the title becomes the commit subject on
  `master`.
- Add or update tests for the behavior that you change.
- Leave `CHANGELOG.md` out. The release workflow builds it from the commit
  history.
- The `ci-gate` and `DCO` checks must pass, and each review thread must be
  resolved before the merge.

### The full evaluation

The full evaluation (`ORAssistant Secret CI`) uses LLM credentials, and each
run costs money. A maintainer starts it on a pull request when the change can
affect answer quality. See [Tests](README.md#tests) in the README.

## Keep secrets out of the repository

Keep credentials in `.env` files and `secret.json`, which Git ignores. The
`detect-private-key` pre-commit hook stops a commit that contains a private
key.
