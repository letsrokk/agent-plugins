# Plugin packages

Each plugin lives in `plugins/<plugin-name>/` and uses [Agent Plugins v1](https://agent-plugins.org/specification) as the shared base, with documented native-loader exceptions. Follow the full [plugin development workflow](../docs/plugin-development.md).

See the [compatibility matrix](../docs/compatibility.md) before claiming support for another harness. Register complete plugin packages so sibling references and bundled scripts remain available.

Every plugin must include:

- `plugin.json` at its root with the Agent Plugins v1 `$schema` or a documented native-loader exception, and a `name` that matches its directory and catalog entries.
- At least one useful component, such as an Agent Skill under `skills/` or an MCP configuration in `mcp.json`.

A Codex-listed plugin must include `.codex-plugin/plugin.json`; its `name` and `version` must match the portable manifest. A Claude Code-listed plugin must include `.claude-plugin/plugin.json`. Keep shared components in portable locations; compatibility manifests contain client-specific discovery, launch, and UI metadata.

Catalog entries always use `./plugins/<plugin-name>` as their source. Add a plugin only to the native catalogs whose installation route has been checked. Copilot and Grok Build use the same shared payload; neither catalog requires a Claude compatibility manifest. See the compatibility matrix for component-specific limits.
