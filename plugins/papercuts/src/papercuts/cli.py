from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from papercuts.models import PapercutsError, PrunePolicy, error_envelope, success_envelope
from papercuts.paths import resolve_storage, set_scope
from papercuts.service import PapercutsService


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PapercutsError("usage", message, exit_status=2)


def _parser() -> _Parser:
    parser = _Parser(prog="papercuts")
    parser.add_argument("--file")
    commands = parser.add_subparsers(dest="command", required=True)

    lodge = commands.add_parser("lodge")
    lodge.add_argument("text")
    lodge.add_argument("--severity", choices=("minor", "major", "blocker"), default="minor")
    lodge.add_argument("--tag", action="append", default=[])
    _evidence_arguments(lodge, include_note=True)

    list_command = commands.add_parser("list")
    list_command.add_argument("--status", choices=("open", "resolved", "all"), default="open")
    list_command.add_argument("--query")
    list_command.add_argument("--tag", action="append", default=[])
    list_command.add_argument("--severity", choices=("minor", "major", "blocker"))
    list_command.add_argument("--min-encounters", type=int)
    list_command.add_argument("--recent-days", type=int)
    list_command.add_argument("--all-projects", action="store_true")
    list_command.add_argument("--limit", type=int, default=50)
    list_command.add_argument("--format", choices=("json", "md"), default="json")

    get = commands.add_parser("get")
    get.add_argument("id")
    get.add_argument("--all-projects", action="store_true")

    vote = commands.add_parser("vote")
    vote.add_argument("id")
    vote.add_argument("--note")
    _evidence_arguments(vote, include_note=False)

    for name in ("resolve", "reopen"):
        status = commands.add_parser(name)
        status.add_argument("id")
        status.add_argument("--note")

    doctor = commands.add_parser("doctor")
    doctor.add_argument("--repair-tail", action="store_true")

    prune = commands.add_parser("prune")
    prune_commands = prune.add_subparsers(dest="prune_command", required=True)
    preview = prune_commands.add_parser("preview")
    _policy_arguments(preview)
    apply = prune_commands.add_parser("apply")
    apply.add_argument("plan_id")
    _policy_arguments(apply)

    config = commands.add_parser("config")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    config_commands.add_parser("show")
    set_scope_command = config_commands.add_parser("set-scope")
    set_scope_command.add_argument("scope", choices=("project", "user"))
    set_scope_command.add_argument("--level", choices=("project", "user"), required=True)
    return parser


def _evidence_arguments(parser: argparse.ArgumentParser, *, include_note: bool) -> None:
    parser.add_argument("--cmd")
    parser.add_argument("--exit", dest="exit_status", type=int)
    parser.add_argument("--stderr-file")
    if include_note:
        parser.add_argument("--evidence")


def _policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--resolved-older-than-days", type=int, default=30)
    parser.add_argument("--open-max-encounters", type=int, default=1)
    parser.add_argument("--open-inactive-for-days", type=int, default=90)
    parser.add_argument("--projects", choices=("current", "all"), default="current")


def main(
    argv: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
    environ: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Parse one command, call the service, and write its public result."""
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    current_directory = cwd or Path.cwd()
    try:
        arguments = _parser().parse_args(argv)
        storage = resolve_storage(
            current_directory,
            explicit_file=Path(arguments.file) if arguments.file else None,
            environ=environ,
        )
        service = PapercutsService(storage)
        data = _dispatch(arguments, service, current_directory)
        if arguments.command == "list" and arguments.format == "md":
            output.write(data + "\n")
        else:
            _write(output, success_envelope(data, journal_path=storage.journal_path))
        return 0
    except PapercutsError as error:
        _write(errors, error_envelope(error))
        return _exit_status(error)


def _dispatch(
    arguments: argparse.Namespace,
    service: PapercutsService,
    cwd: Path,
) -> Any:
    if arguments.command == "lodge":
        return service.lodge(
            arguments.text,
            severity=arguments.severity,
            tags=arguments.tag,
            context=_context(arguments, evidence_note=arguments.evidence, cwd=cwd),
        )
    if arguments.command == "list":
        records = service.list(
            status=arguments.status,
            query=arguments.query,
            tags=arguments.tag,
            severity=arguments.severity,
            min_encounters=arguments.min_encounters,
            recent_days=arguments.recent_days,
            all_projects=arguments.all_projects,
            limit=arguments.limit,
        )
        return _markdown(records) if arguments.format == "md" else records
    if arguments.command == "get":
        return service.get(arguments.id, all_projects=arguments.all_projects)
    if arguments.command == "vote":
        return service.vote(
            arguments.id,
            note=arguments.note,
            context=_context(arguments, cwd=cwd),
        )
    if arguments.command == "resolve":
        return service.resolve(arguments.id, note=arguments.note)
    if arguments.command == "reopen":
        return service.reopen(arguments.id, note=arguments.note)
    if arguments.command == "doctor":
        return service.doctor(repair_tail=arguments.repair_tail)
    if arguments.command == "prune":
        policy = PrunePolicy(
            resolved_older_than_days=arguments.resolved_older_than_days,
            open_max_encounters=arguments.open_max_encounters,
            open_inactive_for_days=arguments.open_inactive_for_days,
            projects=arguments.projects,
        )
        if arguments.prune_command == "preview":
            return service.preview_prune(policy)
        return service.apply_prune(policy, arguments.plan_id)
    if arguments.config_command == "show":
        return service.inspect_storage()
    path = set_scope(cwd, arguments.scope, arguments.level)
    return {"scope": arguments.scope, "level": arguments.level, "path": str(path)}


def _context(
    arguments: argparse.Namespace,
    *,
    cwd: Path,
    evidence_note: str | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    if arguments.cmd is not None:
        context["command"] = arguments.cmd
    if arguments.exit_status is not None:
        context["exit_status"] = arguments.exit_status
    if arguments.stderr_file is not None:
        path = Path(arguments.stderr_file)
        context["stderr_file"] = path if path.is_absolute() else cwd / path
    if evidence_note is not None:
        context["note"] = evidence_note
    return context


def _markdown(records: Sequence[Mapping[str, Any]]) -> str:
    lines = ["# Papercuts"]
    lines.extend(
        "- {id} [{severity}] {encounters} encounters — {project}: {text}".format(
            id=record["id"],
            severity=record["severity"],
            encounters=record["encounter_count"],
            project=record["project"]["name"],
            text=record["text"],
        )
        for record in records
    )
    return "\n".join(lines)


def _exit_status(error: PapercutsError) -> int:
    statuses = {
        "usage": 2,
        "invalid_input": 65,
        "malformed_journal": 65,
        "not_found": 66,
        "ambiguous_id": 66,
        "internal_failure": 70,
        "io_failure": 74,
        "stale_prune_plan": 75,
        "lock_timeout": 75,
        "permission_denied": 77,
        "invalid_config": 78,
    }
    return statuses.get(error.code, 70)


def _write(stream: TextIO, payload: Mapping[str, Any]) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
