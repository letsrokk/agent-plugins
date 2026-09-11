# Rokk Club Agent Plugins

Plugins for Codex and Claude Code that review code, inspect agent configuration, record workflow friction, and help agents write for human readers. Choose individual plugins from the catalogs below; both clients use the same shared [`plugins/`](plugins/README.md) tree.

## Marketplaces

Use a client with plugin marketplace support. Codex reads [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). Run in a terminal:

```sh
codex plugin marketplace add letsrokk/agent-plugins
```

Claude Code reads [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Run inside Claude Code:

```text
/plugin marketplace add letsrokk/agent-plugins
```

Both catalogs reference the same package directories. Packages use the [Agent Plugins v1 specification](https://agent-plugins.org/specification) as a base, with native client manifests where required. See the [compatibility rules](docs/plugin-development.md#choosing-portable-or-native-loading).

Adding a marketplace makes its plugins available; install the ones you want separately. See [Claude Code’s plugin management guide](https://code.claude.com/docs/en/discover-plugins) for client controls.

## Try a plugin

After adding the marketplace, install Agent Doctor to inspect your project’s agent settings.

Codex, in a terminal:

```sh
codex plugin add agent-doctor@rokk-club-codex-plugins
codex plugin list
```

Confirm `agent-doctor` is installed. For Claude Code, run:

```text
/plugin install agent-doctor@rokk-club-claude-plugins
```

Open `/plugin` and confirm Agent Doctor is installed and enabled. Start a fresh session in your project and ask:

```text
Use the inspect-agent-config skill to audit this project’s settings and instructions.
```

Expect findings about the active client’s project configuration, with evidence and suggested fixes. The audit does not change your files. Configuration inspection needs no Node.js runtime; inspecting plugin usage requires Node.js 24 or later. See [Agent Doctor](plugins/agent-doctor/README.md).

Papercuts and Read the Room require Node.js 24 or later on the client process’s `PATH`. For their automatic startup instructions in Codex, review and trust the installed hook in `/hooks`, then start a fresh session. Follow each plugin’s activation instructions below.

## Plugins

### Rokk Club plugins

#### papercuts ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Give coding agents a durable local journal for material workflow friction. See [requirements, privacy, and activation](plugins/papercuts/README.md).

Codex:

```sh
codex plugin add papercuts@rokk-club-codex-plugins
```

Claude:

```text
/plugin install papercuts@rokk-club-claude-plugins
```

#### agent-doctor ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Inspect Codex and Claude Code configuration and count plugin or skill usage in local sessions. See [usage and requirements](plugins/agent-doctor/README.md).

Codex:

```sh
codex plugin add agent-doctor@rokk-club-codex-plugins
```

Claude:

```text
/plugin install agent-doctor@rokk-club-claude-plugins
```

#### read-the-room ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Shape clear communication for human readers across agent sessions, version control, issue trackers, knowledge bases, and chat applications. See [activation and examples](plugins/read-the-room/README.md).

Codex:

```sh
codex plugin add read-the-room@rokk-club-codex-plugins
```

Claude:

```text
/plugin install read-the-room@rokk-club-claude-plugins
```

#### copywriter ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Transform substantive source material into grounded taglines, READMEs, local landing pages, editable pitch decks, and illustrated articles. See [usage and capability requirements](plugins/copywriter/README.md) and the [tested compatibility record](plugins/copywriter/packaging/compatibility.md). End-to-end installed invocation remains unverified in that record. Articles require your draft, outline, or substantive notes.

### Ports

#### eli5 ![Codex](assets/agent-badges/codex.svg)

Explain unfamiliar topics with big visuals and few words. See [an example and port attribution](plugins/eli5/README.md).

Codex:

```sh
codex plugin add eli5@rokk-club-codex-plugins
```

#### pr-review-toolkit ![Codex](assets/agent-badges/codex.svg)

Review pull requests and local changes for bugs, test coverage, comments, error handling, and type invariants. Reviews are advisory; simplification requires an explicit request. See [usage and adaptation details](plugins/pr-review-toolkit/README.md).

Codex:

```sh
codex plugin add pr-review-toolkit@rokk-club-codex-plugins
```

#### code-simplifier ![Codex](assets/agent-badges/codex.svg)

Simplify a precise code scope without changing observable behavior. See [usage and adaptation details](plugins/code-simplifier/README.md).

Codex:

```sh
codex plugin add code-simplifier@rokk-club-codex-plugins
```

## Add a plugin

Follow the full [plugin development workflow](docs/plugin-development.md).

1. Create `plugins/<plugin-name>/plugin.json` using Agent Plugins v1 metadata; follow the documented native-loading exceptions where needed.
2. Add the plugin components in their standard locations.
3. Add the compatibility manifest for each target catalog.
4. Add a matching entry to one or both marketplace catalogs.
5. With Node.js 24 or later, run these commands from the repository root before committing:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run validate
```

The test suite should pass, and validation should print `Marketplace validation passed.` Scripted plugins also require their own test and validation entrypoints; see the development workflow.

## License

This repository is available under the [MIT License](LICENSE). Individual plugins may declare a different license in their own manifests and package files.
