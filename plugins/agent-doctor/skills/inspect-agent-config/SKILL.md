---
name: inspect-agent-config
description: Use when auditing Codex or Claude Code settings, instructions, model or effort choices, ignored configuration, or unexpected agent behavior. For plugin invocation counts, use inspect-plugin-usage.
---

# Inspect Agent Config

Audit the current agent client without changing its files. Separate what is provably wrong from provider guidance and optional experiments.

## Scope

Inspect the current client only: Codex when running in Codex, or Claude Code when running in Claude Code. Do not infer the client from files on disk.

- Default: project scope. An explicit project path bounds reads; otherwise use the current directory as the target and its enclosing project root as the boundary. Ancestor layers outside that boundary remain unseen.
- `user`: user scope only.
- `both`: user and project scopes.

Do not read user files for project-only requests. Resolve `~`, client-home variables, symlinks, and imports locally; report out-of-scope targets without reading them. Never put local paths, configuration content, or values in a web request.

Read the current client's reference once, reusing it while it remains in context:

- Codex: [references/codex.md](references/codex.md)
- Claude Code: [references/claude.md](references/claude.md)

## Audit

1. Fetch only the approved sources needed for the requested question, as routed by the provider reference. Open URLs directly; do not search or follow unrelated links. Follow redirects only within the listed domains. Reuse pages retrieved during this audit and record the retrieval date.
2. Discover in-scope files relevant to the question using the reference and retrieved guidance. A settings-only question need not read instruction bodies; a full audit covers both. Parse configuration before resolving configurable instruction filenames. Inspect installed client version when available; distinguish current documentation from support in that version.
3. Parse TOML or JSON locally and redact secret-like values before returning tool output. Include key names and sanitized values needed for the audit, not whole configuration dumps. Report syntax errors by location without echoing secret-like source lines or guessing intended values.
4. Reconstruct precedence. Label layers as active, shadowed, ignored, or indeterminate with evidence. Missing CLI flags, environment overrides, trust, policy, or runtime state limit claims about effective values; project-only audits cannot establish unseen user defaults.
5. Compare only the requested settings and instructions with retrieved guidance. Derive model advice from current sources and visible client support, never a remembered frontier model. API availability alone does not establish availability in the agent client or account.
6. Keep the audit read-only. For each problem or recommendation, give the file/key, evidence, impact, and smallest suggested edit.

If an approved page is unavailable, finish the local structural audit, mark freshness unverified, and omit current-model or current-recommendation claims that the available pages do not support.

## Report

Lead with findings, separating confirmed problems, provider-supported recommendations, and workload experiments. Include scope, inspected files, relevant precedence, visibility gaps, sources, and retrieval date. Omit empty categories and unrelated settings. For a full audit, summarize the resolved layers in a table; for a narrow question, explain only the relevant chain. Experiments need a tradeoff and an observable way to evaluate them.

For instructions, call out excessive length, vague universal rules, duplicated or conflicting guidance, misplaced one-off workflows, and model-specific prompting that conflicts with the current provider guidance. Quote only the minimum local text needed to identify a problem, and never quote a secret-like value.
