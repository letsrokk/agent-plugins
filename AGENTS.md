# Repository guidelines

This repository publishes two native marketplace catalogs over one shared `plugins/` tree:

- `.agents/plugins/marketplace.json` is the Codex catalog.
- `.claude-plugin/marketplace.json` is the Claude Code catalog.

Preserve this boundary. Do not generate the catalogs or duplicate shared plugin payloads between client-specific trees.

Add plugins one at a time under `plugins/<plugin-name>/`. Every plugin must use the Agent Plugins v1 root `plugin.json`, and its directory name, manifest name, and catalog names must match. Catalog sources must be exactly `./plugins/<plugin-name>`. Add `.claude-plugin/plugin.json` only when the plugin is listed in the Claude Code catalog or otherwise needs Claude-specific metadata.

Keep catalog entries ordered intentionally. Codex entries must include `policy.installation`, `policy.authentication`, and `category`. Use `AVAILABLE` and `ON_INSTALL` unless a plugin has a documented reason to differ.

Repository validation requires Python 3.11 or later. Before committing, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
```
