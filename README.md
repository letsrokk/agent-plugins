# Rokk Club Agent Plugins

Rokk Club publishes portable agent plugins for Codex and Claude Code from one repository. Plugins are added one at a time under [`plugins/`](plugins/README.md).

The marketplaces publish [`papercuts`](plugins/papercuts/README.md) for durable workflow-friction tracking. The Codex marketplace also publishes [`code-simplifier`](plugins/code-simplifier/) for behavior-preserving code cleanup and [`eli5`](plugins/eli5/README.md) for visual explanations.

## Marketplaces

Codex reads `.agents/plugins/marketplace.json` and installs packages that follow the [Agent Plugins v1 specification](https://agent-plugins.org/specification).

```sh
codex plugin marketplace add letsrokk/agent-plugins
```

Claude Code reads `.claude-plugin/marketplace.json`.

```text
/plugin marketplace add letsrokk/agent-plugins
```

Both catalogs reference the same package directories. Portable components stay shared; client-specific manifests and components live beside them only when required.

## Add a plugin

Follow the full [plugin development workflow](docs/plugin-development.md).

1. Create `plugins/<plugin-name>/plugin.json` using the Agent Plugins v1 schema.
2. Add the plugin components in their standard locations.
3. Add the compatibility manifest for each target catalog.
4. Add a matching entry to one or both marketplace catalogs.
5. Run the repository validation commands before committing.

## License

This repository is available under the [MIT License](LICENSE). Individual plugins may declare a different license in their own manifests and package files.
