# Repository guidelines

This repository publishes two native marketplace catalogs over one shared `plugins/` tree:

- `.agents/plugins/marketplace.json` is the Codex catalog.
- `.claude-plugin/marketplace.json` is the Claude Code catalog.

Preserve this boundary. Do not generate the catalogs or duplicate shared plugin payloads between client-specific trees.

Add plugins one at a time under `plugins/<plugin-name>/`. Use Agent Plugins v1 as the base for root `plugin.json` metadata and shared layout. When host support requires native Claude or Codex structures (for example hooks or MCP configuration), use the client manifests and omit the root `$schema` if necessary to select native loading. Document the reason in the plugin README; see `docs/plugin-development.md` for the current compatibility rules. Directory name, manifest names, and catalog names must match. Catalog sources must be exactly `./plugins/<plugin-name>`. Add `.claude-plugin/plugin.json` only when the plugin is listed in the Claude Code catalog or otherwise needs Claude-specific metadata.

Every plugin listed in the Codex catalog must include `.codex-plugin/plugin.json`. Its `name` and non-empty `version` must match the portable root manifest. A discoverable skill on disk requires the Codex compatibility manifest to set `skills` to `"./skills/"`.

A plugin with root `scripts/`, root `src/`, or `skills/*/scripts/` is scripted. It must provide Node.js 24-compatible `scripts/test.js` and `scripts/validate.js` entrypoints that take no arguments, run from the plugin root, and return nonzero on failure. GitHub Actions runs both entrypoints for each changed scripted plugin. Installed plugins require only Node.js; bundle any runtime dependencies and keep npm installation in contributor and CI workflows.

[`docs/plugin-development.md`](docs/plugin-development.md) is the authoritative contributor workflow for manifest roles, local development, and release preparation.

Existing plugins changed without a version update receive an automatic patch bump after validation on `main`. An explicit release version must be a strictly higher stable `MAJOR.MINOR.PATCH` value, synchronized across all existing plugin manifests. New and deleted plugins do not receive automatic bumps.

Keep catalog entries ordered intentionally. Codex entries must include `policy.installation`, `policy.authentication`, and `category`. Use `AVAILABLE` and `ON_INSTALL` unless a plugin has a documented reason to differ.

Repository tooling requires Node.js 24 or later. Install contributor dependencies with `npm ci --ignore-scripts --no-audit --no-fund` at the repository root. Before committing, run:

```sh
npm test
npm run validate
```
