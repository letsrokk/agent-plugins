# Rokk Club Agent Plugins

Rokk Club publishes portable agent plugins for Codex and Claude Code from one repository. Plugins are added one at a time under [`plugins/`](plugins/README.md).

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

## Plugins

### Rokk Club plugins

#### papercuts

![Codex](assets/agent-badges/codex.svg)\
![Claude Code](assets/agent-badges/claude-code.svg)

Give coding agents a durable local journal for material workflow friction.

Codex:

```sh
codex plugin add papercuts@rokk-club-codex-plugins
```

Claude:

```text
/plugin install papercuts@rokk-club-claude-plugins
```

#### agent-doctor

![Codex](assets/agent-badges/codex.svg)\
![Claude Code](assets/agent-badges/claude-code.svg)

Inspect and troubleshoot Codex and Claude configuration, then review recent sessions to count exact plugin or skill usage and summarize successes, problems, and incomplete calls.

Codex:

```sh
codex plugin add agent-doctor@rokk-club-codex-plugins
```

Claude:

```text
/plugin install agent-doctor@rokk-club-claude-plugins
```

#### read-the-room

![Codex](assets/agent-badges/codex.svg)\
![Claude Code](assets/agent-badges/claude-code.svg)

Shape clear communication for human readers across agent sessions, version control, issue trackers, knowledge bases, and chat applications.

Codex:

```sh
codex plugin add read-the-room@rokk-club-codex-plugins
```

Claude:

```text
/plugin install read-the-room@rokk-club-claude-plugins
```

### Ports

#### eli5

![Codex](assets/agent-badges/codex.svg)

Explain any topic with a dead-simple visual explainer that uses big pictures and few words.

Codex:

```sh
codex plugin add eli5@rokk-club-codex-plugins
```

#### pr-review-toolkit

![Codex](assets/agent-badges/codex.svg)

Review pull requests and local changes for code quality, tests, comments, error handling, and type design, then simplify code after the review passes.

Codex:

```sh
codex plugin add pr-review-toolkit@rokk-club-codex-plugins
```

#### code-simplifier

![Codex](assets/agent-badges/codex.svg)

Simplify a precise code scope without changing observable behavior.

Codex:

```sh
codex plugin add code-simplifier@rokk-club-codex-plugins
```

## Add a plugin

Follow the full [plugin development workflow](docs/plugin-development.md).

1. Create `plugins/<plugin-name>/plugin.json` using the Agent Plugins v1 schema.
2. Add the plugin components in their standard locations.
3. Add the compatibility manifest for each target catalog.
4. Add a matching entry to one or both marketplace catalogs.
5. Run the repository validation commands before committing.

## License

This repository is available under the [MIT License](LICENSE). Individual plugins may declare a different license in their own manifests and package files.
