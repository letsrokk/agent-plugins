# Papercuts

Papercuts gives Codex and Claude Code a durable local journal for material engineering friction. During an engineering task, the shared skill searches open complaints in the active project, votes for a clear match, or lodges a concise new complaint. It then continues the task without announcing routine logging.

The skill records dead-end tool calls, misleading documentation, missing helpers, repeated recovery work, configuration footguns, unclear repository instructions, and failures that consume meaningful time. It excludes expected validation failures, corrected typing mistakes, and ordinary unsuccessful searches unless an interface made the failure predictably misleading.

## Requirements and privacy

The CLI requires Python 3.11 or later. The local MCP server also requires [uv](https://docs.astral.sh/uv/); on its first run, `uv` may fetch the pinned `mcp==2.1.1` dependency. The core and CLI have no dependency beyond Python.

Papercuts stores data locally. It has no telemetry and makes no network requests, except for `uv` fetching that pinned MCP dependency on first run. Credential redaction is best effort, not a guarantee: never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence.

Context supports a command up to 1,024 characters, an integer exit status, sanitized stderr up to 4,096 UTF-8 bytes, and a note up to 2,048 characters. Evidence files must be regular files no larger than 1 MiB. Tags are limited to ten.

## Installation

Add this repository's marketplace in the client, then install `papercuts` from that marketplace.

```sh
# Codex CLI
codex plugin marketplace add letsrokk/agent-plugins
codex plugin add papercuts@rokk-club-codex-plugins
```

```text
# Claude Code interactive command
/plugin marketplace add letsrokk/agent-plugins
/plugin install papercuts@rokk-club-claude-plugins
```

## Storage and scope

Papercuts uses a client-specific user journal by default while keeping Codex and
Claude Code storage isolated:

| Client | Project journal | User journal |
| --- | --- | --- |
| Codex | `<project>/.codex/papercuts.jsonl` | `~/.codex/papercuts.jsonl` |
| Claude Code | `<project>/.claude/papercuts.jsonl` | `~/.claude/papercuts.jsonl` |

User-scope lists stay scoped to the current project unless `--all-projects` is supplied.

Codex scope configuration files are `<project>/.codex/papercuts.config.json` and `~/.codex/papercuts.config.json`. Claude Code uses the matching paths under `.claude`. Within the selected client, project configuration takes precedence over user configuration. No configuration, journal, or backup automatically falls back to or migrates from the other client.

The CLI selects the client in this order: `--client`, `PAPERCUTS_CLIENT`, then `codex`. It selects storage in this order: `--file`, `PAPERCUTS_FILE`, project configuration, user configuration, then user scope. Supplying the same explicit file for both clients intentionally shares one journal; this is the only cross-client sharing mechanism.

```sh
# Make this project use a project journal instead of the default user journal.
plugins/papercuts/scripts/papercuts config set-scope project --level project

# Set the default scope in your user configuration.
plugins/papercuts/scripts/papercuts config set-scope user --level user

# Configure Claude Code storage explicitly from the shared CLI.
plugins/papercuts/scripts/papercuts --client claude config set-scope user --level project

# Show the active journal and scope.
plugins/papercuts/scripts/papercuts config show
```

Each event is one JSON object per line in the active `papercuts.jsonl` journal. Codex pruning creates timestamped backups under `.codex/papercuts.backups/`; Claude Code uses `.claude/papercuts.backups/`. The base is the project for project scope and the home directory for user scope. Backups are never removed automatically.

## CLI

All ordinary commands emit one JSON envelope on stdout. Errors emit one structured JSON envelope on stderr. `list --format md` is the only human-readable output mode.

```text
papercuts [--client codex|claude] [--file PATH] lodge TEXT [--severity minor|major|blocker] [--tag TAG] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH] [--evidence NOTE]
papercuts [--client codex|claude] [--file PATH] list [--status open|resolved|all] [--query TEXT] [--tag TAG] [--severity minor|major|blocker] [--min-encounters N] [--recent-days N] [--all-projects] [--limit N] [--format json|md]
papercuts [--client codex|claude] [--file PATH] get ID [--all-projects]
papercuts [--client codex|claude] [--file PATH] vote ID [--note TEXT] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH]
papercuts [--client codex|claude] [--file PATH] resolve ID [--note TEXT]
papercuts [--client codex|claude] [--file PATH] reopen ID [--note TEXT]
papercuts [--client codex|claude] [--file PATH] doctor [--repair-tail]
papercuts [--client codex|claude] [--file PATH] prune preview [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--client codex|claude] [--file PATH] prune apply PLAN_ID [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--client codex|claude] [--file PATH] config show
papercuts [--client codex|claude] [--file PATH] config set-scope project|user --level project|user
```

For example:

```sh
plugins/papercuts/scripts/papercuts lodge "The validator hides the failing manifest path" --severity major --tag tooling
plugins/papercuts/scripts/papercuts list --status open
plugins/papercuts/scripts/papercuts doctor
```

`prune preview` is safe and writes nothing. Before `prune apply PLAN_ID`, inspect the preview and explicitly authorize that exact plan ID. A general request to clean up, authorization for an earlier plan, or a stale plan never authorizes a newly generated plan.

## MCP tools

Codex and Claude Code start the same local stdio MCP server through `scripts/launch-mcp`; each compatibility manifest selects its client storage. Every MCP call requires the active absolute workspace root as `project_root`. The tools are `lodge_complaint`, `list_complaints`, `get_complaint`, `vote_for_complaint`, `resolve_complaint`, `reopen_complaint`, `inspect_storage`, `preview_prune`, and `apply_prune`. MCP cannot set scope or accept an arbitrary journal path.
