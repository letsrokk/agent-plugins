# Plugin development

## Manifest roles

| File | Role |
| --- | --- |
| `plugins/<name>/plugin.json` | Portable Agent Plugins v1 identity and shared package metadata. It must not contain Codex-only `skills`, `mcpServers`, or `interface` fields. |
| `plugins/<name>/.codex-plugin/plugin.json` | Required for Codex catalog entries. It declares Codex discovery routes, MCP launch configuration, and UI metadata. Its `name` and `version` must match the portable manifest. |
| `plugins/<name>/.claude-plugin/plugin.json` | Required only for Claude Code catalog entries. It contains Claude Code-specific metadata and MCP launch configuration. |

Portable skills live under `skills/<skill-name>/SKILL.md`. Codex custom agents live under `skills/<skill-name>/agents/<agent_name>.toml`. Portable MCP configuration may use `mcp.json`; client launch details remain in compatibility manifests when required.

Keep each `SKILL.md` at or below 7,168 bytes to leave headroom when a host loads it into a prompt. Put only universal instructions and routing in the main file. Move task-, channel-, or artifact-specific guidance into focused files under the skill's `references/` directory, and direct the agent to read only the relevant reference. Repository validation enforces the byte limit; check a file directly with `wc -c skills/<skill-name>/SKILL.md`.

See one current plugin package, such as [`plugins/papercuts/`](../plugins/papercuts/), for the package structure. Do not copy its JSON manifests as a second contract.

## Scripted plugin contract

A plugin is scripted when its package contains any of these directories:

- `scripts/`
- `src/`
- `skills/<skill-name>/scripts/`

Every scripted plugin must provide these Python 3.11-compatible entrypoints:

- `scripts/test.py` runs the plugin's tests.
- `scripts/validate.py` runs its static and package-specific validation.

Both entrypoints take no arguments, run from the plugin root, and return zero only when the check passes. They must not prompt, depend on untracked local state, or modify tracked files. Keep dependencies self-contained or install them inside the entrypoint when the plugin already requires that behavior.

Use this test entrypoint for a standard-library `unittest` suite:

```python
#!/usr/bin/env python3
from pathlib import Path
import unittest


plugin_root = Path(__file__).resolve().parents[1]
suite = unittest.defaultTestLoader.discover(str(plugin_root / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
```

Use this validation entrypoint when syntax compilation is the plugin's complete static check:

```python
#!/usr/bin/env python3
from pathlib import Path
import sys
import tokenize


plugin_root = Path(__file__).resolve().parents[1]
failed = False
for directory in ("scripts", "src", "tests"):
    for path in sorted((plugin_root / directory).rglob("*.py")):
        try:
            with tokenize.open(path) as source:
                compile(source.read(), str(path.relative_to(plugin_root)), "exec")
        except (OSError, SyntaxError, UnicodeError) as error:
            print(f"{path.relative_to(plugin_root)}: {error}", file=sys.stderr)
            failed = True
raise SystemExit(1 if failed else 0)
```

GitHub Actions runs both entrypoints on Ubuntu for each changed scripted plugin. A change to this document, the repository instructions, the marketplace validator, the plugin selector, or the validation workflow runs them for every scripted plugin. Skill-only plugins do not need these entrypoints and do not create plugin matrix jobs.

## Create and release a plugin

1. Create `plugins/<name>/plugin.json` with a release version.
2. Add at least one discoverable component.
3. Add the compatibility manifest for each target catalog.
4. Keep every manifest version and any package `__version__` equal.
5. Add catalog entries with exact `./plugins/<name>` sources.
6. If the plugin is scripted, add and run its test and validation entrypoints.
7. Run both repository validation commands.
8. Remove any `+codex.local-*` suffix before a release commit.

Release versions on `main` use stable `MAJOR.MINOR.PATCH` SemVer. A pull request that
changes an existing plugin can leave its version unchanged; after validation succeeds on
`main`, GitHub Actions increments the patch version and synchronizes the portable, Codex,
Claude, and Python version declarations that exist for that plugin. New and deleted plugins
are excluded from automatic bumps.

Set a strictly higher version in the pull request when the change needs an intentional major,
minor, or patch release. Update every existing version declaration together. Pull request
validation rejects malformed, inconsistent, or decreased versions, and the merge automation
preserves a valid higher version without adding another patch bump.

The automation commits generated bumps to `main` as `chore: bump plugin versions`. It retries
against the latest `main` when another merge wins the push race, and a newer version can cover
several changes that merged before the generated commit. The repository `GITHUB_TOKEN` does
not start another workflow run for its own commit, which prevents recursion. The automation
does not create tags, GitHub Releases, or changelogs. Branch protection must allow this
workflow's narrowly scoped `contents: write` job to update `main`.

## Local development and stable reinstall

A configured marketplace name is its identity; the Git marketplace and local worktree cannot coexist under the same top-level marketplace name. A plugin name is its install identity; local development replaces the stable installation unless the developer creates a genuinely separate plugin identity.

Use a disposable development worktree whose local Codex marketplace name is `rokk-club-codex-plugins-dev`, and never commit that local catalog-name change. Validate the repository while the stable marketplace name is present. Then change only the local worktree's top-level marketplace name to `rokk-club-codex-plugins-dev` before local registration, and restore `rokk-club-codex-plugins` before final validation or commit.

For each local iteration, set the same build-metadata version in both the portable and Codex manifests, for example `0.2.0+codex.local-20260901-140000`. Reinstall after each meaningful change, then start a new Codex task so skills and MCP tools reload.

Run the plugin entrypoints from a scripted plugin's root:

```sh
cd plugins/<plugin-name>
python3 scripts/test.py
python3 scripts/validate.py
cd ../..
```

Then run the repository checks and reinstall the plugin:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
codex plugin marketplace add /absolute/path/to/agent-plugins-dev
codex plugin add <plugin-name>@rokk-club-codex-plugins-dev
codex plugin list
```

Test in a new Codex task. Return to the stable build with `codex plugin add <plugin-name>@rokk-club-codex-plugins`; do not edit an installed cache copy.
