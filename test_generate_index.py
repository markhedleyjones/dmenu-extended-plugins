"""Tests for generate_index.py."""

import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _make_repo(tmp_path, index):
    """Lay out a throwaway plugin repo and return its directory."""
    shutil.copy(os.path.join(HERE, "generate_index.py"), tmp_path / "generate_index.py")
    biome = os.path.join(HERE, "biome.json")
    if os.path.exists(biome):
        shutil.copy(biome, tmp_path / "biome.json")
    for name in index:
        (tmp_path / (name + ".py")).write_text(f"# {name}\n")
    (tmp_path / "plugins_index.json").write_text(json.dumps(index))
    return tmp_path


def _run(repo):
    subprocess.run(
        [sys.executable, str(repo / "generate_index.py")], cwd=str(repo), check=True
    )
    return json.loads((repo / "plugins_index.json").read_text())


def test_regenerates_hashes_url_and_drops_min_version(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "plugin_foo": {
                "url": "https://old/master/plugin_foo.py",
                "desc": "Foo plugin",
                "sha1sum": "stale",
                "min_version": 0.0,
                "_min_version_comment": "obsolete",
                "requirements": {"dmenu-extended": ">=1.0.0", "python": ">=3.9"},
                "verified": True,
            }
        },
    )
    entry = _run(repo)["plugin_foo"]
    data = (repo / "plugin_foo.py").read_bytes()

    assert entry["sha256"] == hashlib.sha256(data).hexdigest()
    assert entry["sha1sum"] == hashlib.sha1(data).hexdigest()
    assert entry["url"].endswith("/main/plugin_foo.py")
    assert "min_version" not in entry
    assert "_min_version_comment" not in entry
    # hand-authored metadata is preserved
    assert entry["desc"] == "Foo plugin"
    assert entry["verified"] is True
    assert entry["requirements"] == {"dmenu-extended": ">=1.0.0", "python": ">=3.9"}


def test_entries_sorted_by_name(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "plugin_zebra": {"desc": "z", "requirements": {}},
            "plugin_alpha": {"desc": "a", "requirements": {}},
        },
    )
    assert list(_run(repo).keys()) == ["plugin_alpha", "plugin_zebra"]


def test_idempotent(tmp_path):
    repo = _make_repo(tmp_path, {"plugin_foo": {"desc": "f", "requirements": {}}})
    _run(repo)
    first = (repo / "plugins_index.json").read_text()
    _run(repo)
    second = (repo / "plugins_index.json").read_text()
    assert first == second


def test_missing_plugin_file_is_an_error(tmp_path):
    repo = _make_repo(tmp_path, {"plugin_foo": {"desc": "f", "requirements": {}}})
    (repo / "plugin_foo.py").unlink()
    result = subprocess.run(
        [sys.executable, str(repo / "generate_index.py")],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "no plugin file" in result.stderr
