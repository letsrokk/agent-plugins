# Papercuts

Papercuts gives Codex and Claude Code a durable local journal for material engineering friction. During an engineering task, the shared skill searches open complaints in the active project, votes for a clear match, or lodges a concise new complaint. It then continues the task without announcing routine logging.

The skill records dead-end tool calls, misleading documentation, missing helpers, repeated recovery work, configuration footguns, unclear repository instructions, and failures that consume meaningful time. It excludes expected validation failures, corrected typing mistakes, and ordinary unsuccessful searches unless an interface made the failure predictably misleading.

## Requirements and privacy

The CLI, hooks, and bundled local MCP server require Node.js 24 or later. `node` must be available on the noninteractive client process's `PATH`. Installed plugins need no Python, uv, pip, npm, `node_modules`, or dependency downloads. The CLI and core use Node built-ins; the server includes its pinned official MCP SDK dependencies.

Papercuts stores data locally. It has no telemetry and makes no network requests. Credential redaction is best effort, not a guarantee: never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence.

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

## Session instructions

A synchronous `SessionStart` hook injects the canonical Papercuts skill instructions on startup, resume, clear, and compaction. Its status message is `Loading Papercuts instructions...`. The hook only reads instructions; it does not access journals or create complaints. This makes the logging workflow available without waiting for skill discovery.

After installation or an update, inspect the hook in Codex `/hooks`, review its current definition, and trust it. Start a fresh session and confirm the instructions are present without explicitly invoking the skill. Plugin installation and enablement do not automatically grant hook trust. In Claude Code, verify hook discovery and MCP startup in a fresh session. If a hook or server cannot find `node`, correct the client process's PATH and restart it.

## User storage and migration from 0.2

| Client | Journal |
| --- | --- |
| Codex | `~/.codex/papercuts.jsonl` |
| Claude Code | `~/.claude/papercuts.jsonl` |

Lists stay scoped to the current project unless `--all-projects` is supplied. The CLI selects its client from `--client`, then `PAPERCUTS_CLIENT`, then `codex`. No journal or backup falls back to another client.

Version 0.3 removes project journals, arbitrary journal paths, `--file`, `PAPERCUTS_FILE`, and `config set-scope`. Legacy configuration files selecting `user` are accepted unchanged; project scope, unknown configuration, and old environment overrides fail explicitly. Existing journals and configuration are never moved, merged, overwritten, or deleted automatically.

Before removing obsolete configuration, back up the old journal and any existing destination. If the client user journal does not exist, manually copy the old journal there, preserving its JSONL bytes and restricting its permissions to the current user. If the destination already contains records, retain both backups and review their histories before combining them: concatenating duplicate complaint histories can corrupt the journal. Run `papercuts doctor` after manual migration. Remove the obsolete override only after deciding which user journal should be active. Old Python dependency caches can be removed separately once no older installation uses them.

```sh
plugins/papercuts/scripts/papercuts config show
plugins/papercuts/scripts/papercuts --client claude config show
```

Each event is one JSON object per line. Pruning creates timestamped backups beside the user journal under `papercuts.backups/`; backups are never removed automatically. Existing record IDs and the contract-1 journal format remain compatible.

The home and client directory must be owned by the current user and not writable by other users. New client directories are created with mode 0700; journals and backups use 0600. Existing host directories with mode 0755 are accepted. Journal files must be private regular files with one hard link. Symbolic links and unsafe storage locations are rejected. Node uses supported no-follow flags and identity checks but does not provide Python's directory-relative I/O guarantee against malicious ancestor replacement; use local, user-controlled storage. POSIX mode checks are unavailable on Windows, where the user profile's ACL must restrict writes to its owner.

## CLI

All ordinary commands emit one JSON envelope on stdout. Errors emit one structured JSON envelope on stderr. `list --format md` is the only human-readable output mode.

```text
papercuts [--client codex|claude] lodge TEXT [--severity minor|major|blocker] [--tag TAG] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH] [--evidence NOTE]
papercuts [--client codex|claude] list [--status open|resolved|all] [--query TEXT] [--tag TAG] [--severity minor|major|blocker] [--min-encounters N] [--recent-days N] [--all-projects] [--limit N] [--format json|md]
papercuts [--client codex|claude] get ID [--all-projects]
papercuts [--client codex|claude] vote ID [--note TEXT] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH]
papercuts [--client codex|claude] resolve ID [--note TEXT]
papercuts [--client codex|claude] reopen ID [--note TEXT]
papercuts [--client codex|claude] doctor [--repair-tail]
papercuts [--client codex|claude] prune preview [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--client codex|claude] prune apply PLAN_ID [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--client codex|claude] config show
```

For example:

```sh
plugins/papercuts/scripts/papercuts lodge "The validator hides the failing manifest path" --severity major --tag tooling
plugins/papercuts/scripts/papercuts list --status open
plugins/papercuts/scripts/papercuts doctor
```

`prune preview` is safe and writes nothing. Before `prune apply PLAN_ID`, inspect the preview and explicitly authorize that exact plan ID. A general request to clean up, authorization for an earlier plan, or a stale plan never authorizes a newly generated plan.

## MCP tools

Codex and Claude Code start the same local stdio MCP server through the committed `dist/mcp_server.js` bundle; each compatibility manifest selects its client storage. Every MCP call requires the active absolute workspace root as `project_root`. The tools are `lodge_complaint`, `list_complaints`, `get_complaint`, `vote_for_complaint`, `resolve_complaint`, `reopen_complaint`, `inspect_storage`, `preview_prune`, and `apply_prune`. MCP cannot change storage or accept an arbitrary journal path.

MCP lists and complaint mutation acknowledgments return summaries with ID, text, status, severity, tags, project, encounter count, and last encounter time. Use `get_complaint` for full evidence and history. Automatic duplicate searches request at most five results. CLI output and journal records retain their existing detail.

## Contributor checks

From the plugin directory:

```sh
npm ci --ignore-scripts
npm run build
node scripts/test.js
node scripts/validate.js
```

Commit the lockfile, `dist/mcp_server.js`, and `dist/THIRD_PARTY_NOTICES.txt` together when dependencies or server source change. Validation rebuilds in memory and compares both committed artifacts without rewriting them. Tests use Node's built-in runner, including a packaged-server lifecycle in an installation with spaces and no `node_modules` or tools on PATH. End users do not run npm.

The root manifest retains Agent Plugins v1 metadata but omits `$schema` to select native Codex loading: Codex 0.153.4 otherwise skips hooks and ignores native MCP configuration. See the [manifest compatibility rules](../../docs/plugin-development.md#choosing-portable-or-native-loading).
