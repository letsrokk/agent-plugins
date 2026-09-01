# Plugin development

## Manifest roles

| File | Role |
| --- | --- |
| `plugins/<name>/plugin.json` | Portable Agent Plugins v1 identity and shared package metadata. It must not contain Codex-only `skills`, `mcpServers`, or `interface` fields. |
| `plugins/<name>/.codex-plugin/plugin.json` | Required for Codex catalog entries. It declares Codex discovery routes, MCP launch configuration, and UI metadata. Its `name` and `version` must match the portable manifest. |
| `plugins/<name>/.claude-plugin/plugin.json` | Required only for Claude Code catalog entries. It contains Claude Code-specific metadata and MCP launch configuration. |

Portable skills live under `skills/<skill-name>/SKILL.md`. Codex custom agents live under `skills/<skill-name>/agents/<agent_name>.toml`. Portable MCP configuration may use `mcp.json`; client launch details remain in compatibility manifests when required.

See one current plugin package, such as [`plugins/papercuts/`](../plugins/papercuts/), for the package structure. Do not copy its JSON manifests as a second contract.

## Create and release a plugin

1. Create `plugins/<name>/plugin.json` with a release version.
2. Add at least one discoverable component.
3. Add the compatibility manifest for each target catalog.
4. Keep every manifest version and any package `__version__` equal.
5. Add catalog entries with exact `./plugins/<name>` sources.
6. Run both repository validation commands.
7. Remove any `+codex.local-*` suffix before a release commit.

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

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
codex plugin marketplace add /absolute/path/to/agent-plugins-dev
codex plugin add <plugin-name>@rokk-club-codex-plugins-dev
codex plugin list
```

Test in a new Codex task. Return to the stable build with `codex plugin add <plugin-name>@rokk-club-codex-plugins`; do not edit an installed cache copy.
