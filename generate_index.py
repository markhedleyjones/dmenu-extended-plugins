#!/usr/bin/env python3
"""Regenerate plugins_index.json.

The index is the published manifest dmenu-extended downloads to discover and
verify plugins. This script keeps the hand-authored metadata for each plugin
(``desc``, ``requirements``, ``dependencies``, ``verified``) and regenerates
the machine-derived fields:

* ``url``     - the raw download URL, pinned to the ``main`` branch
* ``sha1sum`` - legacy integrity hash (kept for older clients)
* ``sha256``  - integrity hash the current client prefers

Entries are written sorted by plugin name with a stable field order so the
diff stays clean. Run it after adding or changing any plugin:

    python3 generate_index.py

To add a new plugin, add an entry with its metadata (the computed fields may be
left out - they are filled in here) and re-run.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = "markhedleyjones/dmenu-extended-plugins"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(HERE, "plugins_index.json")
EXAMPLE = "plugin_example.py"

# Fields removed on regeneration (superseded by the requirements field).
DROP_FIELDS = {"min_version", "_min_version_comment"}

# Stable field order for each entry: regenerated fields first, then metadata.
FIELD_ORDER = [
    "url",
    "desc",
    "sha1sum",
    "sha256",
    "requirements",
    "dependencies",
    "verified",
]


def plugin_path(name):
    return os.path.join(HERE, name + ".py")


def file_hashes(path):
    with open(path, "rb") as handle:
        data = handle.read()
    return hashlib.sha1(data).hexdigest(), hashlib.sha256(data).hexdigest()


def regenerate_entry(name, meta):
    path = plugin_path(name)
    if not os.path.exists(path):
        sys.exit(f"error: index entry '{name}' has no plugin file ({name}.py)")
    sha1sum, sha256 = file_hashes(path)

    fields = {key: value for key, value in meta.items() if key not in DROP_FIELDS}
    fields["url"] = f"{RAW_BASE}/{name}.py"
    fields["sha1sum"] = sha1sum
    fields["sha256"] = sha256

    ordered = {key: fields[key] for key in FIELD_ORDER if key in fields}
    for key in sorted(fields):
        ordered.setdefault(key, fields[key])
    return ordered


def warn_unindexed(indexed_names):
    indexed_files = {name + ".py" for name in indexed_names}
    for filename in sorted(os.listdir(HERE)):
        if not (filename.startswith("plugin_") and filename.endswith(".py")):
            continue
        if filename == EXAMPLE or filename in indexed_files:
            continue
        print(
            f"warning: {filename} has no index entry and will not be published",
            file=sys.stderr,
        )


def biome_format(path):
    """Canonicalise JSON with biome so the output matches the repo's formatter.

    biome (a repo dev dependency) collapses short arrays onto one line, which
    json.dump does not; without this the pre-commit biome check would reject
    the generated file.
    """
    biome = shutil.which("biome")
    if biome:
        subprocess.run([biome, "format", "--write", path], check=True)
        return
    print(
        "warning: biome not found on PATH; run 'biome format --write "
        f"{os.path.basename(path)}' before committing",
        file=sys.stderr,
    )


def main():
    with open(INDEX_PATH) as handle:
        index = json.load(handle)

    regenerated = {name: regenerate_entry(name, meta) for name, meta in index.items()}
    ordered_index = {name: regenerated[name] for name in sorted(regenerated)}

    warn_unindexed(ordered_index)

    with open(INDEX_PATH, "w") as handle:
        json.dump(ordered_index, handle, indent=2)
        handle.write("\n")
    biome_format(INDEX_PATH)

    print(f"wrote {INDEX_PATH} ({len(ordered_index)} plugins)")


if __name__ == "__main__":
    main()
