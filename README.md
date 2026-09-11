# Rokk Club Agent Plugins

Give your coding agent more ways to help: review a change, make sense of its settings, explain an unfamiliar topic, or shape an engaging piece of writing.

Rokk Club brings these workflows to Codex and Claude Code as plugins you can install individually. Browse the collection below and choose the ones that fit your work.

## Marketplaces

Start by adding the marketplace for your client, then install a plugin using its command below. The badges show which clients each plugin targets.

For Codex, run in your terminal:

```sh
codex plugin marketplace add letsrokk/agent-plugins
```

For Claude Code, run inside the app:

```text
/plugin marketplace add letsrokk/agent-plugins
```

Papercuts and Read the Room require Node.js 24 or later on your client’s `PATH`. In Codex, review and trust their startup hooks in `/hooks`, then start a fresh session. Other requirements and activation steps are documented in each plugin’s README under [`plugins/`](plugins/README.md).

## Plugins

### Rokk Club plugins

#### papercuts ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Keep a local record of the tool failures, confusing instructions, and recurring snags your agent encounters, so they are available to review later.

Codex:

```sh
codex plugin add papercuts@rokk-club-codex-plugins
```

Claude:

```text
/plugin install papercuts@rokk-club-claude-plugins
```

#### agent-doctor ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Make sense of your agent’s settings and see which plugins and skills it actually uses. Inspect configuration and local session history without changing your files.

Codex:

```sh
codex plugin add agent-doctor@rokk-club-codex-plugins
```

Claude:

```text
/plugin install agent-doctor@rokk-club-claude-plugins
```

#### read-the-room ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Help your agent write for the person reading: clear updates, useful reviews, readable documentation, and chat messages that get to the point.

Codex:

```sh
codex plugin add read-the-room@rokk-club-codex-plugins
```

Claude:

```text
/plugin install read-the-room@rokk-club-claude-plugins
```

#### copywriter ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg)

Turn source material into clear, engaging taglines, READMEs, landing pages, editable pitch decks, and illustrated articles.

Codex:

```sh
codex plugin add copywriter@rokk-club-codex-plugins
```

Claude:

```text
/plugin install copywriter@rokk-club-claude-plugins
```

### Ports

#### eli5 ![Codex](assets/agent-badges/codex.svg)

Make an unfamiliar topic easier to grasp with big visuals and a few well-chosen words.

Codex:

```sh
codex plugin add eli5@rokk-club-codex-plugins
```

#### pr-review-toolkit ![Codex](assets/agent-badges/codex.svg)

Get actionable reviews of pull requests and local changes, covering bugs, tests, comments, error handling, and types. Reviews are advisory; code simplification needs an explicit request.

Codex:

```sh
codex plugin add pr-review-toolkit@rokk-club-codex-plugins
```

#### code-simplifier ![Codex](assets/agent-badges/codex.svg)

Make the code you choose easier to read and maintain while preserving what it does.

Codex:

```sh
codex plugin add code-simplifier@rokk-club-codex-plugins
```

## Try a plugin

After installing Agent Doctor, start a fresh session in your project and ask:

```text
Use the inspect-agent-config skill to audit this project’s settings and instructions.
```

Expect a report explaining configuration problems, suggested fixes, and anything the agent could not verify. The audit leaves your files unchanged.

## Add a plugin

Have a workflow to share? Follow the [plugin development workflow](docs/plugin-development.md). Packages use the [Agent Plugins v1 specification](https://agent-plugins.org/specification) as a base, with native client manifests where needed. The Codex and Claude Code catalogs point to the same shared plugin directories.

1. Create `plugins/<plugin-name>/plugin.json` using the documented manifest rules.
2. Add the plugin components in their standard locations.
3. Add the compatibility manifest for each target catalog.
4. Add a matching entry to one or both marketplace catalogs.
5. With Node.js 24 or later, run the repository checks before committing:

   ```sh
   npm ci --ignore-scripts --no-audit --no-fund
   npm test
   npm run validate
   ```

The tests should pass and validation should print `Marketplace validation passed.` Scripted plugins also need their own test and validation entrypoints, as described in the development workflow.

## License

This repository is available under the [MIT License](LICENSE). Individual plugins may declare a different license in their own manifests and package files.
