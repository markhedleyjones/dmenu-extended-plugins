# dmenu-extended-plugins

A set of plugins for [dmenu-extended](https://github.com/markhedleyjones/dmenu-extended),
and the plugin index it downloads to discover and verify them.

## Using these plugins

Plugins are installed from within dmenu-extended (`-> Settings -> Download more
plugins`). dmenu-extended reads its plugin sources from the `plugin_repositories`
preference; this repository is included by default. You can add your own:

```json
{
  "plugin_repositories": [
    "https://raw.githubusercontent.com/markhedleyjones/dmenu-extended-plugins/main",
    "https://raw.githubusercontent.com/you/your-plugins/main"
  ]
}
```

Each entry is the base URL (or a local path) that contains `plugins_index.json`
and the plugin files. dmenu-extended downloads each plugin over HTTPS and
**verifies its `sha256` before the file is written or run** - a mismatch is
refused. Only add repositories you trust: an installed plugin is executed.

## `plugins_index.json`

A JSON object keyed by plugin module name (`plugin_<name>`). Example entry:

```json
{
  "plugin_internetSearch": {
    "url": "https://raw.githubusercontent.com/markhedleyjones/dmenu-extended-plugins/main/plugin_internetSearch.py",
    "desc": "Adds search providers for faster internet searching",
    "sha1sum": "c0478ef7b409cc686f5380c253249568dbb84d8d",
    "sha256": "b8379d0e3315bb0b00b724a81a476c88a9608b8541a425856ef7c456f08b7fae",
    "requirements": {
      "dmenu-extended": ">=1.0.0",
      "python": ">=3.9"
    },
    "dependencies": {
      "python": ["pexpect"],
      "external": [{ "name": "jrnl", "url": "https://jrnl.sh" }]
    },
    "verified": true
  }
}
```

Generated fields (do not hand-edit - see below):

- **`url`** - raw download URL for the plugin file, pinned to the `main` branch.
- **`sha1sum`** - legacy integrity hash, kept for older clients.
- **`sha256`** - integrity hash the current client verifies against.

Hand-authored metadata (preserved across regeneration):

- **`desc`** - one-line human description.
- **`requirements`** - pip-style version specifiers. `dmenu-extended` is the host
  version, `python` the interpreter (e.g. `">=1.0.0"`).
- **`dependencies`** (optional) - `python` is a list of pip packages, `external`
  a list of `{name, url}` binaries the plugin needs.
- **`verified`** - `true` if the plugin is vetted by the repository maintainers.

## Regenerating the index

Edit the hand-authored metadata in `plugins_index.json`, then run:

```bash
python3 generate_index.py
```

It recomputes `url`, `sha1sum` and `sha256` from the actual plugin files, drops
obsolete fields, sorts the entries, and formats the output with biome. To add a
new plugin, drop `plugin_<name>.py` into the repository root, add an entry with
its metadata (the generated fields may be omitted), and re-run. `plugin_example.py`
is a template and is intentionally not indexed.
