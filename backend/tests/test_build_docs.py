import json
import logging
import subprocess
from pathlib import Path

import pytest

import build_docs


@pytest.fixture
def backend_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run build_docs against an empty backend directory with an empty source map."""
    monkeypatch.setattr(build_docs, "cur_dir", str(tmp_path))
    monkeypatch.setattr(build_docs, "source_dict", {})
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_write_source_list_keeps_sources_from_earlier_steps(backend_dir: Path):
    build_docs.update_src(
        "OpenROAD/docs/build/html/_sources/main/README.md",
        "data/markdown/OR_docs/general/README.md",
    )
    gh_disc_dir = backend_dir / "data/markdown/gh_discussions"
    gh_disc_dir.mkdir(parents=True)
    (gh_disc_dir / "mapping.json").write_text(
        json.dumps({"Bug/1.md": {"url": "https://github.com/discussions/1"}})
    )

    build_docs.write_source_list()

    source_list = json.loads((backend_dir / "data/source_list.json").read_text())
    assert source_list == {
        "data/markdown/OR_docs/general/README.md": (
            "https://openroad.readthedocs.io/en/latest/main/README.html"
        ),
        "data/markdown/gh_discussions/Bug/1.md": "https://github.com/discussions/1",
    }


@pytest.mark.parametrize(
    "build_step",
    [build_docs.build_or_docs, build_docs.build_orfs_docs, build_docs.build_manpages],
)
def test_docs_build_step_fails_when_make_fails(
    backend_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    build_step,
):
    for path in ("OpenROAD/docs", "OpenROAD/src", "OpenROAD-flow-scripts/docs"):
        (backend_dir / path).mkdir(parents=True)

    def fake_run(command, **kwargs):
        returncode = 2 if command.startswith("make") else 0
        return subprocess.CompletedProcess(
            command, returncode, stdout=b"", stderr=b"sphinx: build error"
        )

    monkeypatch.setattr(build_docs.subprocess, "run", fake_run)

    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exit_info:
        build_step()

    assert exit_info.value.code == 1
    assert "exit code 2" in caplog.text
    assert "sphinx: build error" in caplog.text
