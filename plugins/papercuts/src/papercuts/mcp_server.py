from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal, Mapping

from papercuts.models import Client, PapercutsError, PrunePolicy
from papercuts.paths import discover_project, resolve_client, resolve_storage
from papercuts.service import PapercutsService


def service_for_project(
    project_root: str,
    *,
    client: Client = "codex",
) -> PapercutsService:
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
            client=client,
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
    dispatch: dict[
        str, Callable[[PapercutsService, Mapping[str, Any]], dict[str, Any]]
    ] = {
        "lodge_complaint": _lodge_complaint,
        "list_complaints": _list_complaints,
        "get_complaint": _get_complaint,
        "vote_for_complaint": _vote_for_complaint,
        "resolve_complaint": _resolve_complaint,
        "reopen_complaint": _reopen_complaint,
        "inspect_storage": _inspect_storage,
        "preview_prune": _preview_prune,
        "apply_prune": _apply_prune,
    }
    try:
        handler = dispatch.get(name)
        if handler is None:
            raise PapercutsError(
                "invalid_input",
                f"unknown MCP tool: {name}",
                exit_status=65,
            )
        return handler(service, arguments)
    except PapercutsError as error:
        return _error_result(error)


def _invoke_project_tool(
    project_root: str,
    name: str,
    arguments: Mapping[str, Any],
    *,
    client: Client = "codex",
) -> dict[str, Any]:
    try:
        return invoke_tool(
            service_for_project(project_root, client=client),
            name,
            arguments,
        )
    except PapercutsError as error:
        return _error_result(error)


def _error_result(error: PapercutsError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
            "suggested_fix": error.suggested_fix,
        },
    }


def _lodge_complaint(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    result = service.lodge(
        arguments["text"],
        severity=arguments.get("severity", "minor"),
        tags=arguments.get("tags") or (),
        context=_context(arguments, evidence_key="evidence"),
    )
    return {"complaint": _summary(result["record"]), "changed": result["changed"]}


def _list_complaints(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    complaints = service.list(
        status=arguments.get("status", "open"),
        query=arguments.get("query"),
        tags=arguments.get("tags") or (),
        severity=arguments.get("severity"),
        min_encounters=arguments.get("min_encounters"),
        recent_days=arguments.get("recent_days"),
        all_projects=arguments.get("all_projects", False),
        limit=arguments.get("limit", 50),
    )
    return {
        "complaints": [_summary(record) for record in complaints],
        "count": len(complaints),
    }


def _summary(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: record[key]
        for key in (
            "id", "text", "status", "severity", "tags", "project",
            "encounter_count", "last_encounter_at",
        )
    }


def _get_complaint(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "complaint": service.get(
            arguments["complaint_id"],
            all_projects=arguments.get("all_projects", False),
        )
    }


def _vote_for_complaint(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    result = service.vote(
        arguments["complaint_id"],
        note=arguments.get("note"),
        context=_context(arguments),
    )
    return {"complaint": _summary(result["record"]), "changed": result["changed"]}


def _resolve_complaint(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    result = service.resolve(
        arguments["complaint_id"],
        note=arguments.get("note"),
    )
    return {"complaint": _summary(result["record"]), "changed": result["changed"]}


def _reopen_complaint(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    result = service.reopen(
        arguments["complaint_id"],
        note=arguments.get("note"),
    )
    return {"complaint": _summary(result["record"]), "changed": result["changed"]}


def _inspect_storage(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    return {"storage": service.inspect_storage()}


def _preview_prune(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    return {"preview": service.preview_prune(_prune_policy(arguments))}


def _apply_prune(
    service: PapercutsService, arguments: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "result": service.apply_prune(
            _prune_policy(arguments),
            arguments["plan_id"],
        )
    }


def _context(
    arguments: Mapping[str, Any], *, evidence_key: str | None = None
) -> dict[str, Any]:
    context = {
        key: arguments[key]
        for key in ("command", "exit_status", "stderr")
        if arguments.get(key) is not None
    }
    if evidence_key is not None and arguments.get(evidence_key) is not None:
        context["note"] = arguments[evidence_key]
    return context


def _prune_policy(arguments: Mapping[str, Any]) -> PrunePolicy:
    return PrunePolicy(
        resolved_older_than_days=arguments.get("resolved_older_than_days", 30),
        open_max_encounters=arguments.get("open_max_encounters", 1),
        open_inactive_for_days=arguments.get("open_inactive_for_days", 90),
        projects="all" if arguments.get("all_projects", False) else "current",
    )


def create_server(*, client: Client = "codex"):
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
    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    mutation = ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    )

    @server.tool(annotations=mutation)
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
        """Lodge concise workflow friction when no existing open complaint matches."""
        return _invoke_project_tool(
            project_root,
            "lodge_complaint",
            {
                "text": text,
                "severity": severity,
                "tags": tags,
                "command": command,
                "exit_status": exit_status,
                "stderr": stderr,
                "evidence": evidence,
            },
            client=client,
        )

    @server.tool(annotations=read_only)
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
        """Search complaints before lodging new friction or reviewing existing work."""
        return _invoke_project_tool(
            project_root,
            "list_complaints",
            {
                "status": status,
                "query": query,
                "tags": tags,
                "severity": severity,
                "min_encounters": min_encounters,
                "recent_days": recent_days,
                "all_projects": all_projects,
                "limit": limit,
            },
            client=client,
        )

    @server.tool(annotations=read_only)
    def get_complaint(
        project_root: str,
        complaint_id: str,
        all_projects: bool = False,
    ) -> dict[str, Any]:
        """Inspect one complaint by full ID or unique prefix before acting on it."""
        return _invoke_project_tool(
            project_root,
            "get_complaint",
            {"complaint_id": complaint_id, "all_projects": all_projects},
            client=client,
        )

    @server.tool(annotations=mutation)
    def vote_for_complaint(
        project_root: str,
        complaint_id: str,
        note: str | None = None,
        command: str | None = None,
        exit_status: int | None = None,
        stderr: str | None = None,
    ) -> dict[str, Any]:
        """Record another encounter when existing workflow friction clearly matches."""
        return _invoke_project_tool(
            project_root,
            "vote_for_complaint",
            {
                "complaint_id": complaint_id,
                "note": note,
                "command": command,
                "exit_status": exit_status,
                "stderr": stderr,
            },
            client=client,
        )

    @server.tool(annotations=mutation)
    def resolve_complaint(
        project_root: str,
        complaint_id: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a complaint when the workflow friction no longer occurs."""
        return _invoke_project_tool(
            project_root,
            "resolve_complaint",
            {"complaint_id": complaint_id, "note": note},
            client=client,
        )

    @server.tool(annotations=mutation)
    def reopen_complaint(
        project_root: str,
        complaint_id: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Reopen a resolved complaint when the workflow friction returns."""
        return _invoke_project_tool(
            project_root,
            "reopen_complaint",
            {"complaint_id": complaint_id, "note": note},
            client=client,
        )

    @server.tool(annotations=read_only)
    def inspect_storage(project_root: str) -> dict[str, Any]:
        """Inspect the active Papercuts journal location and health without changing it."""
        return _invoke_project_tool(
            project_root,
            "inspect_storage",
            {},
            client=client,
        )

    @server.tool(annotations=read_only)
    def preview_prune(
        project_root: str,
        resolved_older_than_days: int = 30,
        open_max_encounters: int = 1,
        open_inactive_for_days: int = 90,
        all_projects: bool = False,
    ) -> dict[str, Any]:
        """Preview the exact complaints a pruning policy would remove without applying it."""
        return _invoke_project_tool(
            project_root,
            "preview_prune",
            {
                "resolved_older_than_days": resolved_older_than_days,
                "open_max_encounters": open_max_encounters,
                "open_inactive_for_days": open_inactive_for_days,
                "all_projects": all_projects,
            },
            client=client,
        )

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=True,
            idempotent_hint=False,
            open_world_hint=False,
        )
    )
    def apply_prune(
        project_root: str,
        plan_id: str,
        resolved_older_than_days: int = 30,
        open_max_encounters: int = 1,
        open_inactive_for_days: int = 90,
        all_projects: bool = False,
    ) -> dict[str, Any]:
        """Apply the exact preview plan only after explicit user authorization."""
        return _invoke_project_tool(
            project_root,
            "apply_prune",
            {
                "plan_id": plan_id,
                "resolved_older_than_days": resolved_older_than_days,
                "open_max_encounters": open_max_encounters,
                "open_inactive_for_days": open_inactive_for_days,
                "all_projects": all_projects,
            },
            client=client,
        )

    return server


def main() -> None:
    create_server(client=resolve_client(None)).run()


if __name__ == "__main__":
    main()
