# Papercuts Codex Plugin Design

**Date:** 2026-08-31  
**Status:** Approved design  
**Target:** Codex plugin only

## Summary

Add a `papercuts` plugin that gives Codex a durable complaint journal for workflow friction. Codex automatically records material friction while it works, reuses existing complaints when the same problem recurs, and leaves a backlog that people or agents can review and resolve later.

The first release stores complaints locally in append-oriented JSONL, exposes the same behavior through a CLI and a local stdio MCP server, and supports explicit pruning with preview and backup. It ships only in the Codex catalog. The storage and service layers remain independent of Codex paths so a future Claude package can reuse them without adding Claude compatibility code now.

## Goals

- Let Codex lodge material workflow complaints without interrupting its active task.
- Let Codex and users list, inspect, vote for, resolve, and reopen complaints.
- Count every repeated encounter, including repeated encounters from the same agent.
- Default to a project journal at `<project>/.codex/papercuts.jsonl`.
- Allow a user journal at `~/.codex/papercuts.jsonl`.
- Identify the project associated with every journal event.
- Keep normal mutations append-oriented and safe under concurrent agents.
- Let users explicitly preview and apply pruning of old resolved complaints and inactive one-offs.
- Provide stable, structured contracts to both the CLI and MCP clients.

## Non-goals

- Claude manifests, Claude catalog entries, or Claude-specific paths.
- Remote storage, synchronization, accounts, authentication, or telemetry.
- A custom UI.
- Semantic duplicate detection.
- Automatic pruning or backup retention.
- Attachments, arbitrary source files, or raw environment capture.
- A client-abstraction framework or placeholder compatibility files.

## Package layout

```text
plugins/papercuts/
├── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── README.md
├── LICENSE
├── skills/
│   └── papercuts/
│       └── SKILL.md
├── scripts/
│   ├── papercuts
│   └── launch-mcp
├── src/
│   └── papercuts/
│       ├── __init__.py
│       ├── models.py
│       ├── paths.py
│       ├── store.py
│       ├── service.py
│       ├── cli.py
│       └── mcp_server.py
└── tests/
```

The root `plugin.json` is the Agent Plugins v1 manifest required by this repository. `.codex-plugin/plugin.json` contains Codex presentation metadata, the skill path, and an inline Codex MCP server definition. The plugin does not include a root `.mcp.json`; this avoids treating Codex and future Claude launch conventions as interchangeable.

The `scripts/papercuts` launcher runs the standard-library CLI with Python 3.11 or later. `scripts/launch-mcp` uses `uv` with one exact, tested version of the official Python `mcp` SDK. MCP dependencies do not enter the core or CLI runtime.

## Component boundaries

### Models

`models.py` defines versioned journal events, folded complaint views, prune policies, and result envelopes. It does not perform file access or path discovery.

### Path resolution

`paths.py` discovers the current project and resolves Codex storage and configuration. It returns concrete paths and project identity to the service. The store never infers `.codex` paths itself.

### Store

`store.py` owns journal parsing, locking, append operations, folding input, health checks, backups, and atomic replacement during pruning. It has no CLI or MCP types.

### Service

`service.py` is the only implementation of product operations. It receives validated application inputs, resolves exact-duplicate behavior, coordinates store mutations, and returns model objects.

### Adapters

`cli.py` and `mcp_server.py` translate their input and output contracts into service calls. Neither adapter implements complaint rules. This keeps the CLI and MCP behavior equivalent and leaves the service reusable by a future Claude adapter.

### Skill

`skills/papercuts/SKILL.md` tells Codex when and how to record friction, how to search before lodging, what evidence is safe, and when destructive pruning is forbidden. MCP initialization instructions repeat only the short search-before-lodge rule.

## Storage selection

The active journal resolves in this order:

1. CLI `--file <path>`
2. `PAPERCUTS_FILE`
3. `<project>/.codex/papercuts.config.json`
4. `~/.codex/papercuts.config.json`
5. Project scope

The configuration schema is:

```json
{
  "scope": "project"
}
```

Allowed values are `project` and `user`. Project scope resolves to `<project>/.codex/papercuts.jsonl`; user scope resolves to `~/.codex/papercuts.jsonl`. A project configuration takes precedence over the user configuration so one project can select a different scope. The CLI exposes `config show` and `config set-scope --level project|user`; the level selects which configuration file to write. MCP exposes storage information but cannot change configuration.

Project discovery uses the Git worktree root when available and the current working directory otherwise.

## Project identity

Every event contains:

```json
{
  "project": {
    "id": "prj_7e8c...",
    "name": "agent-plugins"
  }
}
```

For Git projects, the ID hashes a normalized remote identity. Normalization removes credentials, treats equivalent SSH and HTTPS forms consistently, removes a trailing `.git`, and normalizes the host. Without a remote, the ID hashes the canonical project root. Only the hash is stored. Absolute roots and remote URLs do not enter the journal. The name is the project directory basename.

In a user-scoped journal, list operations default to the current project. An explicit `all_projects` option reads the cross-project backlog. Complaint identity includes `project.id`, so identical text in different projects remains isolated.

## Journal contract

The journal is JSON Lines with one versioned event per line. Common fields are `contract`, `kind`, `ts`, `agent`, and `project`.

### Complaint

```json
{
  "contract": 1,
  "kind": "complaint",
  "id": "pc_9f2c41d0a8b3",
  "ts": "2026-08-31T12:00:00Z",
  "agent": "codex",
  "project": {"id": "prj_7e8c", "name": "agent-plugins"},
  "text": "The validator hides the invalid manifest path.",
  "severity": "minor",
  "tags": ["tooling"],
  "context": {}
}
```

Severity is `minor`, `major`, or `blocker`. Tags are lower-case, deduplicated, sorted, and limited to ten.

The complaint ID is content-addressed from contract version, project ID, normalized text, and normalized tags. The service verifies the complete identity when an abbreviated hash matches, so it never merges a hash collision.

### Encounter

```json
{
  "contract": 1,
  "kind": "encounter",
  "complaint_id": "pc_9f2c41d0a8b3",
  "ts": "2026-08-31T13:00:00Z",
  "agent": "codex",
  "project": {"id": "prj_7e8c", "name": "agent-plugins"},
  "note": "The same failure occurred during marketplace validation.",
  "context": {}
}
```

Each vote appends one encounter. The first complaint event is also an occurrence, so folded views expose both `encounter_count` (complaint plus votes) and `vote_count` (encounter events only).

### Status events

`resolved` and `reopened` events contain `complaint_id`, an optional note, and the common fields. Folding events in journal order determines current status and status history.

Resolving an already resolved complaint and reopening an open complaint are successful no-ops with `changed: false`. Voting for or lodging an exact duplicate of a resolved complaint appends a reopening event followed by an encounter within one locked mutation.

### Folded complaint

A folded complaint includes its original fields plus:

- current status;
- `encounter_count` and `vote_count`;
- `last_encounter_at`;
- the latest resolution note;
- bounded recent encounters;
- status history.

Open lists use a fixed v1 sort: severity, encounter count, last encounter, then stable ID.

## Evidence limits

Context may include a command, exit status, sanitized stderr, and a short free-form note. Limits are:

- command: 1,024 characters;
- note: 2,048 characters;
- sanitized stderr: 4,096 UTF-8 bytes;
- evidence file input: regular files no larger than 1 MiB;
- tags: ten.

The service applies best-effort credential redaction before persistence. It rejects environment dumps, non-regular evidence files, and oversize inputs. The skill states that redaction is not a guarantee and instructs Codex never to submit secrets or raw environments.

## Operations

The service and CLI provide:

- `lodge`
- `list`
- `get`
- `vote`
- `resolve`
- `reopen`
- `doctor`
- prune preview and apply
- configuration show and set-scope

Lodging an exact duplicate of an open complaint appends an encounter instead of another complaint. Semantic similarity is not inferred.

The MCP server exposes:

- `lodge_complaint`
- `list_complaints`
- `get_complaint`
- `vote_for_complaint`
- `resolve_complaint`
- `reopen_complaint`
- `inspect_storage`
- `preview_prune`
- `apply_prune`

Each tool has an explicit input schema and structured output. Read operations carry read-only annotations. Lodge, vote, resolve, and reopen are mutating but non-destructive. `apply_prune` is destructive. MCP does not expose configuration mutation or arbitrary journal paths.

Every MCP tool requires an absolute `project_root`. The skill supplies the active workspace root on each call. The server validates that it names an existing directory, derives project identity from it, and then applies the normal project or user scope configuration. The server does not infer the project from its process working directory because a bundled MCP server runs from the plugin installation directory. It also does not depend on MCP roots discovery, which is deprecated in the current protocol. CLI calls continue to discover the project from their working directory.

CLI stdout contains one JSON envelope per command. Errors use one structured envelope on stderr and a nonzero exit. `list --format md` is the only human-oriented stdout mode. Empty list results are successful.

## Automatic agent behavior

When Codex encounters material workflow friction, the skill directs it to:

1. Search open complaints in the current project with a short query and relevant tags.
2. Vote with a concise encounter note when a clear match exists.
3. Otherwise lodge a complaint that states what happened and what would have prevented it.
4. Continue the active task without announcing routine logging.

Material friction includes dead-end tool calls, misleading documentation, missing helpers, repeated manual recovery, configuration footguns, unclear repository instructions, and failures that consume meaningful time. Expected validation failures, corrected typing mistakes, and ordinary unsuccessful searches are excluded unless the interface made the failure predictably misleading.

Pruning never runs automatically. Codex may preview pruning when asked. It may apply a preview only after the user explicitly authorizes that exact plan. Resolve and reopen may occur autonomously when they directly reflect verified work, with a concise reason recorded.

## Concurrency and journal health

Mutations use an adjacent lock directory acquired with atomic directory creation and a bounded retry loop. Lock metadata records a unique owner token, process, host, and creation time. A lock may be recovered automatically only when it is older than the recovery threshold and the implementation can establish that its local owner is absent. Otherwise the operation returns a retryable lock-timeout error and `doctor` explains manual recovery.

Within the lock, appends write complete UTF-8 records, flush, and sync before release. Readers tolerate only an incomplete final line, which can result from an interrupted write. A malformed interior line makes the journal unhealthy and blocks mutation. `doctor` reports exact line numbers. It repairs an incomplete trailing line only when the user explicitly requests repair and the exclusive lock is held.

Mutation refuses journal and backup targets that traverse symlinks. Newly created user files use owner-only permissions where supported.

## Pruning

The default prune policy is:

```json
{
  "resolved_older_than_days": 30,
  "open_max_encounters": 1,
  "open_inactive_for_days": 90,
  "projects": "current"
}
```

A resolved complaint qualifies after the retention period. An open complaint qualifies only when its encounter count is at or below the threshold and its last encounter is older than the inactivity threshold. Users may override every threshold and may select all projects in a user journal.

Preview folds the current journal, explains every candidate, reports estimated removed complaints, events, and bytes, and returns a plan ID. The plan ID hashes the journal bytes, normalized policy, and selected complaint IDs. Preview writes nothing.

Apply requires the plan ID and the same policy. Under the exclusive lock it recomputes the journal digest and refuses a stale plan. It then:

1. writes a timestamped backup;
2. writes every surviving complaint history to a temporary journal;
3. flushes and syncs the temporary journal;
4. atomically replaces the active journal;
5. reports the backup and actual reclaimed counts.

Project backups live at `.codex/papercuts.backups/`; user backups live at `~/.codex/papercuts.backups/`. Backups are never removed automatically.

## Error contract

Public errors have stable string codes and documented retryability. The initial set covers:

- invalid input;
- complaint not found or ambiguous ID prefix;
- malformed journal;
- stale prune plan;
- lock timeout;
- permission denied;
- invalid configuration;
- I/O failure;
- internal failure.

The CLI maps these to stable exit statuses and includes a concise suggested fix where one is actionable. MCP returns the same error code and message as structured content.

## Codex packaging

Only `.agents/plugins/marketplace.json` receives a `papercuts` entry. It uses source `./plugins/papercuts`, category `Developer Tools`, installation `AVAILABLE`, and authentication `ON_INSTALL`. `.claude-plugin/marketplace.json` remains unchanged, and the plugin contains no `.claude-plugin/plugin.json`.

`.codex-plugin/plugin.json` declares the skill and an inline local stdio MCP server. The inline definition launches `scripts/launch-mcp` relative to the plugin root. This client-specific launch metadata is deliberately separate from the shared server implementation.

Future Claude work can add `.claude-plugin/plugin.json` with its own inline MCP launch definition and `.claude` path resolver defaults. The Python service, journal contract, CLI, and server implementation do not change. This design does not promise that Codex and Claude will share one journal; a future Claude design must decide that explicitly.

## Verification

Repository validation remains:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
```

Plugin-specific coverage follows the repository's minimal test policy:

- one main-path test proves lodge, exact-duplicate encounter, vote, resolve, automatic reopen, filtering, folded counts, and representative CLI and MCP translation through the shared service;
- one critical-failure test proves that a stale prune plan cannot replace a changed journal and leaves both journal and backup state correct.

Manual verification exercises the launchers, `doctor`, project and user path selection, and repository marketplace validation.

## Acceptance criteria

- Installing the Codex plugin makes the papercuts skill and MCP tools available.
- Codex automatically records material friction according to the skill without stopping its task.
- Project storage is the default and user storage can be selected through configuration.
- Every persisted event identifies its project without storing a remote URL or absolute root.
- Exact duplicate lodging and explicit voting produce encounter events rather than duplicate complaints.
- Resolve, reopen, list, get, and doctor behave consistently through CLI and MCP.
- Concurrent mutations cannot interleave JSON records.
- Pruning cannot run without an explicit preview plan, refuses stale plans, creates a backup, and atomically replaces the journal.
- No Claude files or Claude catalog changes are included.
- Both repository validation commands pass.
