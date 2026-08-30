# Plugin packages

Each plugin lives in `plugins/<plugin-name>/` and uses the portable [Agent Plugins v1](https://agent-plugins.org/specification) package format.

Every plugin must include:

- `plugin.json` at its root with the Agent Plugins v1 `$schema` and a `name` that matches its directory and catalog entries.
- At least one useful component, such as an Agent Skill under `skills/` or an MCP configuration in `mcp.json`.

A plugin listed in the Claude Code marketplace must also include `.claude-plugin/plugin.json`. Keep shared components in their portable locations; add client-specific files only where the portable standard does not cover the capability.

Catalog entries always use `./plugins/<plugin-name>` as their source. Add a plugin to the Codex catalog, the Claude Code catalog, or both according to the clients it supports.
