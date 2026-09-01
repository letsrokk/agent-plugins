# Papercuts Codex Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Codex-only `papercuts` plugin that automatically records workflow friction in a configurable JSONL journal and exposes review, encounter voting, lifecycle, health, and explicitly authorized pruning through a CLI and MCP tools.

**Architecture:** A Python 3.11 standard-library core owns project identity, storage resolution, event folding, locking, and product operations. Thin CLI and MCP adapters call one service API; the Codex manifest supplies client-specific MCP launch metadata while shared Python code remains usable by a future Claude package.

**Tech Stack:** Python 3.11+, `unittest`, JSONL, `argparse`, SHA-256, local stdio MCP with `mcp==2.1.1`, `uv`, Agent Plugins v1 manifests.

**Spec:** `docs/superpowers/specs/2026-08-31-papercuts-plugin-design.md`

## Global Constraints

- Ship only in `.agents/plugins/marketplace.json`; do not modify `.claude-plugin/marketplace.json` or add `.claude-plugin/plugin.json`.
- Use project storage at `<project>/.codex/papercuts.jsonl` by default and user storage at `~/.codex/papercuts.jsonl` when configured.
- Keep the core and CLI dependency-free on Python 3.11 or later; pin the MCP runtime to exactly `mcp==2.1.1` through `uv`.
- Store no raw remote URL, absolute project root, secret, raw environment dump, or unbounded evidence in journal events.
- Keep normal mutations append-oriented; only explicitly authorized prune apply may rewrite the journal, and it must create a backup first.
- Use encounter-based voting; every vote appends an encounter even when the same agent voted before.
- Require an absolute `project_root` on every MCP call; do not infer the active project from the MCP process working directory or deprecated MCP roots discovery.
- Add only one main-path plugin test and one critical-failure plugin test, in line with the repository test policy.
- Use `apply_patch` for source and documentation edits. Preserve all unrelated worktree changes.
- Run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate_marketplaces.py` before completion.

## File map

| Path | Responsibility |
| --- | --- |
| `plugins/papercuts/plugin.json` | Portable Agent Plugins v1 metadata |
| `plugins/papercuts/.codex-plugin/plugin.json` | Codex metadata, skill registration, and inline MCP launch definition |
| `plugins/papercuts/skills/papercuts/SKILL.md` | Automatic friction-capture workflow and prune authorization rule |
| `plugins/papercuts/scripts/papercuts` | Dependency-free CLI launcher |
| `plugins/papercuts/scripts/launch-mcp` | Pinned `uv` MCP launcher |
| `plugins/papercuts/src/papercuts/models.py` | Public constants, dataclasses, normalization, errors, and JSON envelopes |
| `plugins/papercuts/src/papercuts/paths.py` | Project discovery, project identity, config precedence, and scope writes |
| `plugins/papercuts/src/papercuts/store.py` | Locking, JSONL reads/appends, folding input, doctor, digest, backup, and replacement |
| `plugins/papercuts/src/papercuts/service.py` | All complaint, lifecycle, list, health, and prune behavior |
| `plugins/papercuts/src/papercuts/cli.py` | `argparse` command contract and JSON/Markdown output |
| `plugins/papercuts/src/papercuts/mcp_server.py` | MCP tool schemas, annotations, service translation, and stdio entry point |
| `plugins/papercuts/tests/test_papercuts.py` | Exactly one main-path test and one critical prune-failure test |
| `.agents/plugins/marketplace.json` | Codex marketplace entry |

---

### Task 1: Core contracts and Codex storage resolution

**Files:**
- Create: `plugins/papercuts/src/papercuts/__init__.py`
- Create: `plugins/papercuts/src/papercuts/models.py`
- Create: `plugins/papercuts/src/papercuts/paths.py`
- Create: `plugins/papercuts/tests/test_papercuts.py`

**Interfaces:**
- Produces: `ProjectRef`, `StorageContext`, `PrunePolicy`, `PapercutsError`, `success_envelope()`, and `error_envelope()` from `papercuts.models`.
- Produces: `discover_project()`, `project_ref()`, `resolve_storage()`, and `set_scope()` from `papercuts.paths`.
- `resolve_storage(cwd, *, explicit_file=None, environ=None, home=None, project_root=None, remote_url=None) -> StorageContext` is the shared path entry point used by the CLI and service factory.

- [ ] **Step 1: Verify the repository baseline before adding production code**

Run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
```

Expected: both commands exit 0. If either fails, stop and report the pre-existing failure instead of changing unrelated code.

- [ ] **Step 2: Write the initial main-path test for project identity and scope resolution**

Create the test module with one main-path method. This method will be extended in later tasks rather than creating more main-path tests.

```python
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PLUGIN_SRC))

from papercuts.paths import project_ref, resolve_storage, set_scope


class PapercutsPluginTests(unittest.TestCase):
    def test_main_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "agent-plugins"
            home = Path(directory) / "home"
            root.mkdir()
            home.mkdir()

            project = project_ref(
                root,
                "git@github.com:letsrokk/agent-plugins.git",
            )
            equivalent = project_ref(
                root,
                "https://github.com/letsrokk/agent-plugins",
            )
            self.assertEqual(project.id, equivalent.id)
            self.assertEqual(project.name, "agent-plugins")
            self.assertNotIn(str(root), json.dumps(project.to_dict()))
            self.assertNotIn("github.com", project.id)

            storage = resolve_storage(
                root,
                home=home,
                project_root=root,
                remote_url="git@github.com:letsrokk/agent-plugins.git",
            )
            self.assertEqual(storage.scope, "project")
            self.assertEqual(storage.journal_path, root / ".codex/papercuts.jsonl")

            config_path = set_scope(root, "user", "project", home=home)
            self.assertEqual(config_path, root / ".codex/papercuts.config.json")
            storage = resolve_storage(
                root,
                home=home,
                project_root=root,
                remote_url="git@github.com:letsrokk/agent-plugins.git",
            )
            self.assertEqual(storage.scope, "user")
            self.assertEqual(storage.journal_path, home / ".codex/papercuts.jsonl")
```

- [ ] **Step 3: Run the focused test and confirm the missing package failure**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
```

Expected: FAIL because `papercuts.paths` does not exist.

- [ ] **Step 4: Implement the public models and error envelope**

Define these exact public types in `models.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Scope = Literal["project", "user"]
Severity = Literal["minor", "major", "blocker"]
Status = Literal["open", "resolved"]


@dataclass(frozen=True)
class ProjectRef:
    id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class StorageContext:
    project: ProjectRef
    project_root: Path
    journal_path: Path
    scope: Scope
    config_source: Path | None


@dataclass(frozen=True)
class PrunePolicy:
    resolved_older_than_days: int = 30
    open_max_encounters: int = 1
    open_inactive_for_days: int = 90
    projects: Literal["current", "all"] = "current"

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


class PapercutsError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_status: int,
        retryable: bool = False,
        suggested_fix: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_status = exit_status
        self.retryable = retryable
        self.suggested_fix = suggested_fix


def success_envelope(data: Any, *, journal_path: Path) -> dict[str, Any]:
    return {"ok": True, "data": data, "meta": {"contract": 1, "file": str(journal_path)}}


def error_envelope(error: PapercutsError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
            "suggested_fix": error.suggested_fix,
        },
        "meta": {"contract": 1},
    }
```

Export `__version__ = "0.1.0"` from `__init__.py`.

- [ ] **Step 5: Implement project and storage resolution**

Implement these exact signatures in `paths.py`:

```python
def discover_project(cwd: Path) -> tuple[Path, str | None]:
    """Return the Git worktree root and sanitized remote input, or cwd and None."""


def project_ref(root: Path, remote_url: str | None) -> ProjectRef:
    """Hash normalized remote identity, falling back to the canonical root."""


def resolve_storage(
    cwd: Path,
    *,
    explicit_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    project_root: Path | None = None,
    remote_url: str | None = None,
) -> StorageContext:
    """Apply explicit file, environment, project config, user config, default precedence."""


def set_scope(
    cwd: Path,
    scope: Scope,
    level: Literal["project", "user"],
    *,
    home: Path | None = None,
) -> Path:
    """Atomically write one scope configuration and return its path."""
```

Normalize `ssh://git@host/owner/repo`, `git@host:owner/repo`, and `https://host/owner/repo` to `host/owner/repo` before hashing. Strip credentials, query strings, fragments, trailing slash, and `.git`; lower-case only the host. Use `prj_` plus the first 16 SHA-256 hex characters. Read configuration as strict JSON containing only `scope`; raise `PapercutsError(code="invalid_config", exit_status=78)` for malformed or unknown values. Write config through a sibling temporary file and `os.replace`.

- [ ] **Step 6: Run the focused and repository tests**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
python3 -m unittest discover -s tests -v
```

Expected: both pass; the plugin suite contains exactly one test at this stage.

- [ ] **Step 7: Commit the storage contract**

```sh
git add plugins/papercuts/src/papercuts plugins/papercuts/tests/test_papercuts.py
git commit -m "feat: add papercuts storage resolution"
```

---

### Task 2: Append-oriented journal and complaint lifecycle service

**Files:**
- Create: `plugins/papercuts/src/papercuts/store.py`
- Create: `plugins/papercuts/src/papercuts/service.py`
- Modify: `plugins/papercuts/tests/test_papercuts.py`

**Interfaces:**
- Consumes: `ProjectRef`, `StorageContext`, `PapercutsError`, and severity/status literals from Task 1.
- Produces: `JournalStore(path)`, `fold_events(events)`, and `PapercutsService(storage, *, agent="codex", now=None)`.
- Service methods return JSON-serializable dictionaries: `lodge`, `list`, `get`, `vote`, `resolve`, `reopen`, and `inspect_storage`.

- [ ] **Step 1: Extend the single main-path test with lifecycle behavior**

Append these imports and assertions to the existing test method. Use an iterator-backed clock so journal bytes are deterministic.

```python
from datetime import datetime, timezone

from papercuts.service import PapercutsService

# Inside test_main_path, after storage resolution:
times = iter(
    datetime(2026, 8, 31, hour, tzinfo=timezone.utc)
    for hour in range(10, 20)
)
service = PapercutsService(storage, now=lambda: next(times))

lodged = service.lodge(
    "Validator hides the invalid manifest path",
    severity="major",
    tags=["tooling", "validator"],
)
complaint_id = lodged["record"]["id"]
self.assertTrue(lodged["changed"])
self.assertEqual(lodged["record"]["encounter_count"], 1)

duplicate = service.lodge(
    "  Validator hides the invalid manifest path  ",
    severity="minor",
    tags=["validator", "tooling"],
)
self.assertEqual(duplicate["record"]["id"], complaint_id)
self.assertEqual(duplicate["record"]["vote_count"], 1)

voted = service.vote(complaint_id[:8], note="Repeated during catalog validation")
self.assertEqual(voted["record"]["encounter_count"], 3)

resolved = service.resolve(complaint_id, note="Validator now reports the path")
self.assertEqual(resolved["record"]["status"], "resolved")

recurred = service.vote(complaint_id, note="Regression in a new validation run")
self.assertEqual(recurred["record"]["status"], "open")
self.assertEqual(recurred["record"]["vote_count"], 3)

listed = service.list(query="manifest", tags=["tooling"])
self.assertEqual([item["id"] for item in listed], [complaint_id])
self.assertEqual(service.get(complaint_id[:8])["id"], complaint_id)
```

- [ ] **Step 2: Run the focused test and confirm the missing service failure**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
```

Expected: FAIL because `papercuts.service` does not exist.

- [ ] **Step 3: Implement safe JSONL reading, folding, and locked appends**

Implement `JournalStore` with these methods:

```python
class JournalStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read_events(self) -> list[dict[str, Any]]:
        """Parse complete UTF-8 JSON object lines and reject malformed interiors."""

    @contextmanager
    def mutation(self) -> Iterator[list[dict[str, Any]]]:
        """Acquire the adjacent lock directory, read current events, and release safely."""

    def append_events_locked(self, events: Sequence[dict[str, Any]]) -> None:
        """Append complete compact JSON records, flush, and fsync before return."""

    def digest(self) -> str:
        """Return SHA-256 of current journal bytes, with empty bytes for a missing file."""
```

Use `<journal>.lock` as the adjacent lock directory. Its metadata JSON contains `token`, `pid`, `host`, and `created_at`. Retry for five seconds with bounded jitter. Recover only a lock older than five minutes whose host is local and whose process is confirmed absent. Otherwise raise `PapercutsError(code="lock_timeout", exit_status=75, retryable=True)`. Remove the lock only when its token still matches the owner.

Validate that each event has `contract == 1`, a supported `kind`, the common fields, and project identity. Ignore an incomplete final line during reads; reject malformed complete or interior lines with `code="malformed_journal"` and exit 65. Before mutation, reject symlink components from the existing ancestor through the journal target.

A mutation must also refuse to append when an incomplete final line exists, returning `malformed_journal` with a suggested `doctor --repair-tail` fix. This prevents a new event from being concatenated onto torn bytes. Only the explicit doctor repair path may truncate that tail.

Implement `fold_events(events) -> dict[str, dict[str, Any]]`. Preserve complaint fields, count complaint plus encounters, record vote count separately, fold status in order, retain status history, and retain only the ten newest encounter details. Reject orphan events and mismatched event project IDs.

- [ ] **Step 4: Implement service lifecycle operations**

Use this service surface and centralize all mutation decisions inside its lock:

```python
class PapercutsService:
    def __init__(
        self,
        storage: StorageContext,
        *,
        agent: str = "codex",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.storage = storage
        self.store = JournalStore(storage.journal_path)
        self.agent = agent
        self.now = now or (lambda: datetime.now(timezone.utc))

    def lodge(self, text: str, *, severity: Severity = "minor", tags: Sequence[str] = (), context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Create a complaint or append an encounter for an exact duplicate."""

    def list(self, *, status: Status | Literal["all"] = "open", query: str | None = None, tags: Sequence[str] = (), severity: Severity | None = None, min_encounters: int | None = None, recent_days: int | None = None, all_projects: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        """Return folded complaints using the fixed v1 ordering."""

    def get(self, complaint_id: str, *, all_projects: bool = False) -> dict[str, Any]:
        """Resolve a full or unique prefix ID and return one folded complaint."""

    def vote(self, complaint_id: str, *, note: str | None = None, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Append one encounter, reopening first when required."""

    def resolve(self, complaint_id: str, *, note: str | None = None) -> dict[str, Any]:
        """Append resolved unless already resolved."""

    def reopen(self, complaint_id: str, *, note: str | None = None) -> dict[str, Any]:
        """Append reopened unless already open."""

    def inspect_storage(self) -> dict[str, Any]:
        """Return scope, path, project, byte count, event count, and health."""
```

Normalize complaint text by trimming and collapsing whitespace. Normalize tags by trimming, lower-casing, deduplicating, and sorting. Build complaint IDs from contract, project ID, normalized text, and tags using SHA-256 with prefix `pc_` and 16 hex characters. On a hash match, verify full normalized identity before treating it as a duplicate.

Use the fixed open-list order: blocker before major before minor, then higher encounter count, newer encounter timestamp, and stable ID. Filter user-scope results to the current project unless `all_projects=True`. A missing or ambiguous prefix raises `not_found` or `ambiguous_id` with exit 66.

- [ ] **Step 5: Run the main-path and repository tests**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
python3 -m unittest discover -s tests -v
```

Expected: pass with one plugin test. Inspect the generated journal and confirm each non-empty line parses as one JSON object.

- [ ] **Step 6: Commit the lifecycle service**

```sh
git add plugins/papercuts/src/papercuts plugins/papercuts/tests/test_papercuts.py
git commit -m "feat: add papercuts complaint lifecycle"
```

---

### Task 3: Evidence safety, doctor, and explicit pruning

**Files:**
- Modify: `plugins/papercuts/src/papercuts/models.py`
- Modify: `plugins/papercuts/src/papercuts/store.py`
- Modify: `plugins/papercuts/src/papercuts/service.py`
- Modify: `plugins/papercuts/tests/test_papercuts.py`

**Interfaces:**
- Consumes: `JournalStore`, `fold_events`, and lifecycle methods from Task 2.
- Produces: `sanitize_context()`, `JournalStore.doctor()`, `JournalStore.replace_locked()`, `PapercutsService.preview_prune()`, and `PapercutsService.apply_prune()`.
- `preview_prune(policy: PrunePolicy) -> dict[str, Any]` returns the plan ID, normalized policy, candidates, and estimated counts.
- `apply_prune(policy: PrunePolicy, plan_id: str) -> dict[str, Any]` verifies freshness, backs up, and atomically replaces.

- [ ] **Step 1: Add the one critical-failure test for stale pruning**

Add one second test method and no other plugin test methods:

```python
from papercuts.models import PapercutsError, PrunePolicy


def test_stale_prune_plan_cannot_replace_changed_journal(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        home = Path(directory) / "home"
        root.mkdir()
        home.mkdir()
        storage = resolve_storage(root, home=home, project_root=root, remote_url=None)
        moments = iter(
            [
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                datetime(2026, 8, 31, tzinfo=timezone.utc),
                datetime(2026, 8, 31, 1, tzinfo=timezone.utc),
                datetime(2026, 8, 31, 2, tzinfo=timezone.utc),
            ]
        )
        service = PapercutsService(storage, now=lambda: next(moments))
        old = service.lodge("One-off obsolete friction")["record"]["id"]
        preview = service.preview_prune(PrunePolicy())
        self.assertEqual([item["id"] for item in preview["candidates"]], [old])

        service.lodge("New complaint after preview", tags=["new"])
        before = storage.journal_path.read_bytes()

        with self.assertRaises(PapercutsError) as raised:
            service.apply_prune(PrunePolicy(), preview["plan_id"])

        self.assertEqual(raised.exception.code, "stale_prune_plan")
        self.assertEqual(storage.journal_path.read_bytes(), before)
        backup_dir = root / ".codex/papercuts.backups"
        self.assertFalse(backup_dir.exists())
```

Extend `test_main_path` with one doctor assertion after the lifecycle assertions:

```python
health = service.doctor()
self.assertTrue(health["healthy"])
self.assertGreaterEqual(health["event_count"], 6)
```

- [ ] **Step 2: Run the focused test and verify missing prune behavior**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
```

Expected: FAIL because `preview_prune`, `apply_prune`, and `doctor` do not exist.

- [ ] **Step 3: Implement bounded evidence sanitization and health reporting**

Add `sanitize_context(context) -> dict[str, Any]` in `models.py`. Accept only `command`, `exit_status`, `stderr`, `stderr_file`, and `note`. Enforce command 1,024 characters, note 2,048 characters, and sanitized stderr 4,096 UTF-8 bytes. For `stderr_file`, require a regular file no larger than 1 MiB before reading. Reject keys suggesting full environments, including `env`, `environment`, and `environ`.

Redact common bearer tokens, URL credentials, GitHub-style tokens, OpenAI-style keys, and assignments whose key contains `TOKEN`, `SECRET`, `PASSWORD`, or `API_KEY`. Apply limits after redaction. Raise `invalid_input` with exit 65 for invalid evidence.

Implement:

```python
def doctor(self, *, repair_tail: bool = False) -> dict[str, Any]:
    """Report health and optionally truncate only an incomplete final record."""

def replace_locked(
    self,
    surviving_events: Sequence[dict[str, Any]],
    *,
    backup_dir: Path,
    timestamp: datetime,
) -> Path:
    """Write backup and fsynced temporary journal, then os.replace the journal."""
```

`doctor(repair_tail=True)` must acquire the mutation lock, preserve all complete bytes, truncate only the incomplete tail, and report `repaired: true`. It must never repair malformed complete or interior records.

- [ ] **Step 4: Implement deterministic preview and atomic prune apply**

Implement service methods with exact policy validation:

```python
def doctor(self, *, repair_tail: bool = False) -> dict[str, Any]:
    return self.store.doctor(repair_tail=repair_tail)

def preview_prune(self, policy: PrunePolicy) -> dict[str, Any]:
    """Select whole complaint histories and hash journal bytes, policy, and IDs."""

def apply_prune(self, policy: PrunePolicy, plan_id: str) -> dict[str, Any]:
    """Recompute preview under lock, reject stale plans, back up, and replace."""
```

Validate non-negative day thresholds and encounter counts. Resolved complaints qualify by latest resolution timestamp. Open complaints qualify only when both the maximum encounter and inactivity rules hold. Honor `projects="current"` even in a shared user journal. Sort candidate IDs before hashing. Compute plan ID as `pp_` plus 24 SHA-256 hex characters over journal digest, canonical JSON policy, and canonical candidate IDs.

Under the mutation lock, recompute the digest and candidate set before creating a backup. On mismatch raise `stale_prune_plan` with exit 75 and `retryable=True`. Write project backups under `<project>/.codex/papercuts.backups` and user backups under `~/.codex/papercuts.backups`. Do not create a backup when the plan is stale or has no candidates.

- [ ] **Step 5: Run both plugin tests and repository tests**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
python3 -m unittest discover -s tests -v
```

Expected: exactly two plugin tests pass; the stale-plan test leaves the journal byte-identical and creates no backup.

- [ ] **Step 6: Commit safety and pruning**

```sh
git add plugins/papercuts/src/papercuts plugins/papercuts/tests/test_papercuts.py
git commit -m "feat: add safe papercuts pruning"
```

---

### Task 4: JSON-first CLI and configuration commands

**Files:**
- Create: `plugins/papercuts/src/papercuts/cli.py`
- Create: `plugins/papercuts/scripts/papercuts`
- Modify: `plugins/papercuts/tests/test_papercuts.py`

**Interfaces:**
- Consumes: `resolve_storage`, `set_scope`, envelopes, `PrunePolicy`, and every service method.
- Produces: `main(argv=None, *, cwd=None, environ=None, stdout=None, stderr=None) -> int` and executable `scripts/papercuts`.

- [ ] **Step 1: Extend the existing main-path test with a representative CLI call**

Add imports and assertions inside `test_main_path`; do not create another test:

```python
import io

from papercuts.cli import main as cli_main

cli_out = io.StringIO()
cli_err = io.StringIO()
exit_status = cli_main(
    [
        "--file",
        str(storage.journal_path),
        "list",
        "--status",
        "all",
        "--all-projects",
    ],
    cwd=root,
    environ={},
    stdout=cli_out,
    stderr=cli_err,
)
self.assertEqual(exit_status, 0)
self.assertEqual(cli_err.getvalue(), "")
cli_payload = json.loads(cli_out.getvalue())
self.assertTrue(cli_payload["ok"])
self.assertEqual(cli_payload["meta"]["contract"], 1)
self.assertEqual(cli_payload["data"][0]["id"], complaint_id)
```

- [ ] **Step 2: Run the focused test and confirm the missing CLI failure**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
```

Expected: FAIL because `papercuts.cli` does not exist.

- [ ] **Step 3: Implement the complete argparse surface**

Build one parser with global `--file` and these subcommands:

```text
lodge TEXT [--severity minor|major|blocker] [--tag TAG] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH] [--evidence NOTE]
list [--status open|resolved|all] [--query TEXT] [--tag TAG] [--severity VALUE] [--min-encounters N] [--recent-days N] [--all-projects] [--limit N] [--format json|md]
get ID [--all-projects]
vote ID [--note TEXT] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH]
resolve ID [--note TEXT]
reopen ID [--note TEXT]
doctor [--repair-tail]
prune preview [policy flags]
prune apply PLAN_ID [policy flags]
config show
config set-scope project|user --level project|user
```

Use this exact entry-point signature:

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
    environ: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Parse one command, call the service, and write exactly one result envelope."""
```

Catch only `PapercutsError` for public failures. Emit compact, sorted JSON plus one newline. Do not print progress. `--format md` is valid only for list and renders a heading plus one bullet per complaint containing ID, severity, encounters, project name, and text. Empty results exit 0.

Map errors to the stable statuses from the design: usage 2, invalid input or malformed journal 65, not found or ambiguous 66, internal 70, I/O 74, stale plan or lock timeout 75, permission 77, and configuration 78.

- [ ] **Step 4: Add the dependency-free CLI launcher**

Create an executable POSIX launcher with no stdout output:

```sh
#!/bin/sh
set -eu

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$plugin_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m papercuts.cli "$@"
```

Set its executable bit. The Python module must include `if __name__ == "__main__": raise SystemExit(main())`.

- [ ] **Step 5: Run focused tests and a real launcher smoke check**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
temporary_directory=$(mktemp -d)
plugins/papercuts/scripts/papercuts --file "$temporary_directory/papercuts.jsonl" lodge "Smoke-test friction" --tag test
plugins/papercuts/scripts/papercuts --file "$temporary_directory/papercuts.jsonl" list --status all
```

Expected: tests pass; each launcher call writes one JSON envelope and no stderr. Leave the generated directory under the system temporary directory for automatic cleanup after inspection.

- [ ] **Step 6: Commit the CLI**

```sh
git add plugins/papercuts/src/papercuts/cli.py plugins/papercuts/scripts/papercuts plugins/papercuts/tests/test_papercuts.py
git commit -m "feat: add papercuts CLI"
```

---

### Task 5: Local stdio MCP adapter

**Files:**
- Create: `plugins/papercuts/src/papercuts/mcp_server.py`
- Create: `plugins/papercuts/scripts/launch-mcp`
- Modify: `plugins/papercuts/tests/test_papercuts.py`

**Interfaces:**
- Consumes: `PapercutsService`, `resolve_storage`, and all model/service types.
- Produces: `service_for_project(project_root)`, `invoke_tool(service, name, arguments)`, `create_server()`, and executable `scripts/launch-mcp`.
- Every MCP tool requires `project_root: str`; no MCP tool accepts an arbitrary journal path or changes configuration.

- [ ] **Step 1: Extend the existing main-path test with pure MCP translation**

Add these assertions inside `test_main_path` without importing the external SDK:

```python
from papercuts.mcp_server import invoke_tool

mcp_result = invoke_tool(
    service,
    "list_complaints",
    {"status": "all", "query": "manifest", "limit": 10},
)
self.assertEqual(mcp_result["complaints"][0]["id"], complaint_id)
self.assertEqual(mcp_result["count"], 1)
```

- [ ] **Step 2: Run the focused test and confirm the missing MCP adapter failure**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
```

Expected: FAIL because `papercuts.mcp_server` does not exist. The failure must not attempt to install `mcp`; SDK imports remain inside `create_server()`.

- [ ] **Step 3: Implement SDK-independent dispatch and project validation**

Implement:

```python
def service_for_project(project_root: str) -> PapercutsService:
    root = Path(project_root)
    if not root.is_absolute() or not root.is_dir():
        raise PapercutsError(
            "invalid_input",
            "project_root must be an existing absolute directory",
            exit_status=65,
        )
    discovered_root, remote_url = discover_project(root)
    return PapercutsService(
        resolve_storage(
            discovered_root,
            project_root=discovered_root,
            remote_url=remote_url,
        )
    )


def invoke_tool(
    service: PapercutsService,
    name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    """Map one known MCP operation to the shared service and shape its result."""
```

Use an explicit dispatch dictionary, reject unknown names, and return named structured fields such as `complaint`, `complaints`, `count`, `preview`, `result`, or `storage`. Convert `PapercutsError` into `{"ok": False, "error": {"code": error.code, "message": error.message, "retryable": error.retryable, "suggested_fix": error.suggested_fix}}`; do not log user data.

- [ ] **Step 4: Register all nine MCP tools with accurate annotations**

Import SDK symbols only inside `create_server()`:

```python
def create_server():
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer(
        "papercuts",
        instructions=(
            "When material workflow friction occurs, search open complaints in the active "
            "project. Vote for a clear match; otherwise lodge a concise complaint. Never "
            "apply pruning without explicit user authorization for the preview plan."
        ),
    )
```

Register `lodge_complaint`, `list_complaints`, `get_complaint`, `vote_for_complaint`, `resolve_complaint`, `reopen_complaint`, `inspect_storage`, `preview_prune`, and `apply_prune`. Each function takes `project_root: str` plus typed operation inputs, obtains `service_for_project(project_root)`, and calls `invoke_tool`.

Use these exact nested function signatures so generated schemas stay stable:

```python
def lodge_complaint(
    project_root: str,
    text: str,
    severity: Literal["minor", "major", "blocker"] = "minor",
    tags: list[str] | None = None,
    command: str | None = None,
    exit_status: int | None = None,
    stderr: str | None = None,
    evidence: str | None = None,
) -> dict[str, Any]:

def list_complaints(
    project_root: str,
    status: Literal["open", "resolved", "all"] = "open",
    query: str | None = None,
    tags: list[str] | None = None,
    severity: Literal["minor", "major", "blocker"] | None = None,
    min_encounters: int | None = None,
    recent_days: int | None = None,
    all_projects: bool = False,
    limit: int = 50,
) -> dict[str, Any]:

def get_complaint(
    project_root: str,
    complaint_id: str,
    all_projects: bool = False,
) -> dict[str, Any]:

def vote_for_complaint(
    project_root: str,
    complaint_id: str,
    note: str | None = None,
    command: str | None = None,
    exit_status: int | None = None,
    stderr: str | None = None,
) -> dict[str, Any]:

def resolve_complaint(
    project_root: str,
    complaint_id: str,
    note: str | None = None,
) -> dict[str, Any]:

def reopen_complaint(
    project_root: str,
    complaint_id: str,
    note: str | None = None,
) -> dict[str, Any]:

def inspect_storage(project_root: str) -> dict[str, Any]:

def preview_prune(
    project_root: str,
    resolved_older_than_days: int = 30,
    open_max_encounters: int = 1,
    open_inactive_for_days: int = 90,
    all_projects: bool = False,
) -> dict[str, Any]:

def apply_prune(
    project_root: str,
    plan_id: str,
    resolved_older_than_days: int = 30,
    open_max_encounters: int = 1,
    open_inactive_for_days: int = 90,
    all_projects: bool = False,
) -> dict[str, Any]:
```

Build context dictionaries only from non-`None` evidence arguments. Convert `all_projects` to `PrunePolicy.projects` as `"all"` or `"current"`. Tool docstrings must say when the tool is appropriate, and `apply_prune` must state that the exact preview requires explicit user authorization.

Use `ToolAnnotations(read_only_hint=True, open_world_hint=False)` for list, get, inspect, and preview. For lodge, vote, resolve, and reopen use `read_only_hint=False`, `destructive_hint=False`, `idempotent_hint=False`, and `open_world_hint=False`. For apply prune use `read_only_hint=False`, `destructive_hint=True`, `idempotent_hint=False`, and `open_world_hint=False`.

End the module with:

```python
def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
```

Never print to stdout; use standard-library logging, which writes to stderr.

- [ ] **Step 5: Add the pinned MCP launcher**

Create an executable launcher:

```sh
#!/bin/sh
set -eu

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if ! command -v uv >/dev/null 2>&1; then
    echo "papercuts MCP requires uv: https://docs.astral.sh/uv/" >&2
    exit 78
fi
export PYTHONPATH="$plugin_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec uv run --quiet --with mcp==2.1.1 -- python -m papercuts.mcp_server
```

Set the executable bit. Do not add a virtual environment, lockfile, requirements file, or fallback installer.

- [ ] **Step 6: Verify tests and MCP registration**

Run:

```sh
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
PYTHONPATH=plugins/papercuts/src uv run --with mcp==2.1.1 -- python -c 'import asyncio; from papercuts.mcp_server import create_server; print([tool.name for tool in asyncio.run(create_server().list_tools())])'
```

Expected: exactly two tests pass. The second command lists exactly the nine tool names and emits no server protocol output.

- [ ] **Step 7: Commit the MCP adapter**

```sh
git add plugins/papercuts/src/papercuts/mcp_server.py plugins/papercuts/scripts/launch-mcp plugins/papercuts/tests/test_papercuts.py
git commit -m "feat: expose papercuts MCP tools"
```

---

### Task 6: Skill, plugin manifests, marketplace entry, and end-to-end validation

**Files:**
- Create: `plugins/papercuts/plugin.json`
- Create: `plugins/papercuts/.codex-plugin/plugin.json`
- Create: `plugins/papercuts/skills/papercuts/SKILL.md`
- Create: `plugins/papercuts/README.md`
- Create: `plugins/papercuts/LICENSE`
- Modify: `.agents/plugins/marketplace.json`

**Interfaces:**
- Consumes: executable `scripts/launch-mcp`, all nine MCP tools, and the CLI from earlier tasks.
- Produces: installable Codex plugin `papercuts` version `0.1.0` and one Codex marketplace entry.

- [ ] **Step 1: Add the portable and Codex manifests**

Create `plugins/papercuts/plugin.json` with the exact portable fields accepted by this repository:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "papercuts",
  "version": "0.1.0",
  "description": "Give Codex a durable complaint journal for workflow friction.",
  "author": {
    "name": "Rokk Club",
    "url": "https://github.com/letsrokk"
  },
  "homepage": "https://github.com/letsrokk/agent-plugins",
  "repository": "https://github.com/letsrokk/agent-plugins",
  "license": "MIT",
  "keywords": ["codex", "friction", "feedback", "developer-tools"]
}
```

Create `.codex-plugin/plugin.json` with version `0.1.0`, the same publisher metadata, `skills: "./skills/"`, and this MCP block:

```json
{
  "mcpServers": {
    "papercuts": {
      "command": "./scripts/launch-mcp",
      "cwd": "."
    }
  }
}
```

Its interface uses display name `Papercuts`, category `Developer Tools`, capabilities `Interactive`, `Read`, and `Write`, website `https://github.com/letsrokk/agent-plugins`, and default prompts `Review the open papercuts for this project.` and `Preview stale papercuts that may be pruned.` Do not declare apps, hooks, icons, logos, screenshots, privacy URLs, or Claude metadata.

- [ ] **Step 2: Write the automatic-lodging skill**

Use this exact frontmatter and preserve the behavioral rules from the spec:

```markdown
---
name: papercuts
description: Use during any engineering task when Codex encounters material friction in tools, documentation, configuration, repository instructions, or repeated recovery work. Search and record the friction without interrupting the active task. Also use when the user asks to review, vote on, resolve, reopen, inspect, or prune papercuts.
---
```

The body must instruct Codex to pass the active absolute workspace root as `project_root`, search open complaints first, vote on a clear match, lodge otherwise, and continue the active task without announcing routine logging. Include the exact evidence limits and exclusions from the design. State that `preview_prune` is allowed on request but `apply_prune` requires explicit authorization for that exact plan ID. State that resolution and reopening require verified evidence and a concise note.

- [ ] **Step 3: Add README and MIT license**

Document:

- automatic lodging behavior;
- project and user storage paths;
- `config set-scope` examples;
- all CLI commands;
- the JSONL event and backup locations;
- pruning preview/apply with explicit authorization;
- Python 3.11 and `uv` requirements;
- best-effort redaction warning;
- no telemetry or network access except `uv` fetching the pinned MCP dependency on first run.

Add `plugins/papercuts/LICENSE` with the same MIT license text and 2026 Rokk Club copyright as the repository root license.

- [ ] **Step 4: Append only the Codex marketplace entry**

Append after `eli5` in `.agents/plugins/marketplace.json`:

```json
{
  "name": "papercuts",
  "source": {
    "source": "local",
    "path": "./plugins/papercuts"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Developer Tools"
}
```

Confirm `.claude-plugin/marketplace.json` is byte-identical to its pre-task state.

- [ ] **Step 5: Validate the plugin package and repository**

Run:

```sh
python3 /Users/rokk/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/papercuts
python3 -m unittest plugins/papercuts/tests/test_papercuts.py -v
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
git diff --check
```

Expected: every command exits 0; the plugin suite reports exactly two tests.

- [ ] **Step 6: Perform end-to-end CLI and MCP smoke checks**

Use a fresh exact temporary directory:

```sh
temporary_directory=$(mktemp -d)
plugins/papercuts/scripts/papercuts --file "$temporary_directory/papercuts.jsonl" lodge "Smoke-test complaint" --tag smoke
plugins/papercuts/scripts/papercuts --file "$temporary_directory/papercuts.jsonl" list --status all
PYTHONPATH=plugins/papercuts/src uv run --with mcp==2.1.1 -- python -c 'import asyncio; from papercuts.mcp_server import create_server; print(len(asyncio.run(create_server().list_tools())))'
```

Expected: both CLI commands return successful JSON envelopes; the MCP check prints `9`. Inspect the temporary journal for valid one-object-per-line JSON and leave its generated directory under the system temporary directory for automatic cleanup.

- [ ] **Step 7: Review scope and commit the finished plugin**

Run:

```sh
git status --short
git diff -- .claude-plugin/marketplace.json
```

Expected: only the Papercuts plugin, Codex marketplace entry, and approved documentation changes appear; the Claude diff is empty.

Commit:

```sh
git add plugins/papercuts .agents/plugins/marketplace.json
git commit -m "feat: add papercuts Codex plugin"
```

After the commit, run the repository validation commands once more and report their exact pass counts.
