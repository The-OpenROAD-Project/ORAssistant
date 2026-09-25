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


def fake_publications_download(monkeypatch: pytest.MonkeyPatch, page: str) -> list[str]:
    """Serve page as the publications page and fake wget. Return the URLs."""
    monkeypatch.setattr(
        build_docs.requests,
        "get",
        lambda url: type("Response", (), {"text": page})(),
    )
    downloads = []

    def fake_wget(command, **kwargs):
        _, url, _, output = command
        downloads.append(url)
        Path(output).write_bytes(b"%PDF")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(build_docs.subprocess, "run", fake_wget)
    return downloads


def test_get_or_publications_downloads_each_paper_once(
    backend_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(build_docs, "EXTRA_PAPERS", [])
    paper_url = "https://vlsicad.ucsd.edu/Publications/Conferences/390/c390.pdf"
    other_url = "https://vlsicad.ucsd.edu/Publications/Conferences/391/c391.pdf"
    page = f"""
        <a href="{paper_url}">Paper title</a> <a href="{paper_url}">PDF</a>
        <a href="{other_url}">PDF</a>
    """
    downloads = fake_publications_download(monkeypatch, page)
    pdf_dir = backend_dir / "data/pdf/OR_publications"
    pdf_dir.mkdir(parents=True)

    build_docs.get_or_publications()

    assert downloads == [paper_url, other_url]
    assert sorted(p.name for p in pdf_dir.iterdir()) == ["c390.pdf", "c391.pdf"]
    assert build_docs.source_dict == {
        "data/pdf/OR_publications/c390.pdf": paper_url,
        "data/pdf/OR_publications/c391.pdf": other_url,
    }


def test_get_or_publications_adds_extra_papers_not_on_the_page(
    backend_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    listed_url = "https://vlsicad.ucsd.edu/Publications/Conferences/389/c389.pdf"
    extra_url = "https://arxiv.org/pdf/2304.11761v2"
    monkeypatch.setattr(
        build_docs,
        "EXTRA_PAPERS",
        [(listed_url, "RTL-MP.pdf"), (extra_url, "Hier-RTLMP.pdf")],
    )
    downloads = fake_publications_download(
        monkeypatch, f'<a href="{listed_url}">PDF</a>'
    )
    pdf_dir = backend_dir / "data/pdf/OR_publications"
    pdf_dir.mkdir(parents=True)

    build_docs.get_or_publications()

    assert downloads == [listed_url, extra_url]
    assert sorted(p.name for p in pdf_dir.iterdir()) == ["Hier-RTLMP.pdf", "c389.pdf"]
    assert build_docs.source_dict == {
        "data/pdf/OR_publications/c389.pdf": listed_url,
        "data/pdf/OR_publications/Hier-RTLMP.pdf": extra_url,
    }


def test_extra_papers_have_unique_pdf_file_names():
    names = [name for _, name in build_docs.EXTRA_PAPERS]
    assert len(set(names)) == len(names)
    assert all(name.endswith(".pdf") for name in names)


def test_repo_commit_env_override_skips_ls_remote(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OR_REPO_COMMIT", "abc123")

    def fail_run(command, **kwargs):
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(build_docs.subprocess, "run", fail_run)

    assert (
        build_docs.resolve_repo_commit("OR_REPO_COMMIT", build_docs.OR_REPO_URL)
        == "abc123"
    )


def test_repo_commit_defaults_to_master_head(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ORFS_REPO_COMMIT", raising=False)
    head = "2bf0c95e8bbfc87bf7002690c2f47006cf0a71a7"
    commands = []

    def fake_ls_remote(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=f"{head}\trefs/heads/master\n", stderr=""
        )

    monkeypatch.setattr(build_docs.subprocess, "run", fake_ls_remote)

    commit = build_docs.resolve_repo_commit(
        "ORFS_REPO_COMMIT", build_docs.ORFS_REPO_URL
    )

    assert commit == head
    assert commands == [
        ["git", "ls-remote", build_docs.ORFS_REPO_URL, "refs/heads/master"]
    ]


@pytest.mark.parametrize(
    "result",
    [
        subprocess.CompletedProcess([], 128, stdout="", stderr="fatal: no access"),
        subprocess.CompletedProcess([], 0, stdout="", stderr=""),
    ],
)
def test_repo_commit_fails_when_master_is_not_resolved(
    monkeypatch: pytest.MonkeyPatch, result: subprocess.CompletedProcess
):
    monkeypatch.delenv("OR_REPO_COMMIT", raising=False)
    monkeypatch.setattr(build_docs.subprocess, "run", lambda command, **kw: result)

    with pytest.raises(SystemExit) as exit_info:
        build_docs.resolve_repo_commit("OR_REPO_COMMIT", build_docs.OR_REPO_URL)

    assert exit_info.value.code == 1


def test_write_build_info_records_inputs_and_paper_urls(backend_dir: Path):
    (backend_dir / "data").mkdir()
    build_docs.source_dict.update(
        {
            "data/pdf/OR_publications/c391.pdf": "https://example.org/c391.pdf",
            "data/pdf/OR_publications/c390.pdf": "https://example.org/c390.pdf",
            "data/pdf/OpenSTA/OpenSTA_docs.pdf": "https://example.org/OpenSTA.pdf",
            "data/markdown/OR_docs/general/README.md": "https://example.org/README",
        }
    )
    commits = {"OpenROAD": "a" * 40, "OpenROAD-flow-scripts": "b" * 40}

    build_docs.write_build_info(commits, crawl_date="2026-09-25T12:00:00Z")

    build_info = json.loads((backend_dir / "data/BUILD_INFO.json").read_text())
    assert build_info == {
        "crawl_date": "2026-09-25T12:00:00Z",
        "commits": {
            "OpenROAD": "a" * 40,
            "OpenROAD-flow-scripts": "b" * 40,
            "OpenSTA": build_docs.opensta_repo_commit,
        },
        "gh_discussions_revision": build_docs.GH_DISCUSSIONS_REVISION,
        "paper_urls": [
            "https://example.org/c390.pdf",
            "https://example.org/c391.pdf",
        ],
    }


def write_page(site: Path, path: str, body: str) -> None:
    page = site / path / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(f"<html><body>{body}</body></html>")


def test_prune_or_website_removes_listing_pages_and_duplicates(tmp_path: Path):
    site = tmp_path / "theopenroadproject.org"
    article = "<h1>2023 review</h1><p>OpenROAD grew in 2023.</p>"
    write_page(site, "2023-review", article)
    write_page(site, "news/2023-review", f"\n  {article}\n")
    write_page(site, "av1-encoder", "<p>OpenROAD™ builds the encoder.OpenLane too.</p>")
    write_page(
        site, "news/av1-encoder1", "<p>OpenROAD builds the encoder. OpenLane too</p>"
    )
    write_page(site, "news/replace-open-sourcing", "<p>RePlAce is open.</p>")
    write_page(site, "news/replace-open-sourcing-2", "<p>RePlAce v1.1 is out.</p>")
    write_page(site, "about-us", "<p>About</p>")
    write_page(site, "our-team", "<p>About</p>")
    write_page(site, "events-2024-recap", "<p>Recap of the events.</p>")
    for listing in (
        "feed",
        "blogs",
        "blogs/page/2",
        "event",
        "event/page/10",
        "news-category/latest-news",
        "news-category/latest-news/feed",
        "wp-json",
    ):
        write_page(site, listing, f"<p>{article} and more posts</p>")

    build_docs.prune_or_website(str(tmp_path))

    remaining = sorted(
        str(p.parent.relative_to(site)) for p in site.rglob("index.html")
    )
    assert remaining == [
        "about-us",
        "events-2024-recap",
        "news/2023-review",
        "news/av1-encoder1",
        "news/replace-open-sourcing",
        "news/replace-open-sourcing-2",
    ]
