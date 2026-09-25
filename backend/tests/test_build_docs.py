import json
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
