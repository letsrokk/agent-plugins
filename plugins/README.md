# Plugin packages

Each plugin lives in `plugins/<plugin-name>/` and uses the portable [Agent Plugins v1](https://agent-plugins.org/specification) package format. Follow the full [plugin development workflow](../docs/plugin-development.md).

Every plugin must include:

- `plugin.json` at its root with the Agent Plugins v1 `$schema` and a `name` that matches its directory and catalog entries.
- At least one useful component, such as an Agent Skill under `skills/` or an MCP configuration in `mcp.json`.

A Codex-listed plugin must include `.codex-plugin/plugin.json`; its `name` and `version` must match the portable manifest. A Claude Code-listed plugin must include `.claude-plugin/plugin.json`. Keep shared components in portable locations; compatibility manifests contain client-specific discovery, launch, and UI metadata.

Catalog entries always use `./plugins/<plugin-name>` as their source. Add a plugin to the Codex catalog, the Claude Code catalog, or both according to the clients it supports.
