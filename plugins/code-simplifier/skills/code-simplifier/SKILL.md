---
name: code-simplifier
description: Use when code should be simplified without behavior changes, either for an explicit project scope, current uncommitted changes, or an associated pull request or merge request.
---

# Code Simplifier

Adapted from Anthropic's Code Simplifier plugin for Codex. See the plugin-level `NOTICE` for source and modification details.

Resolve one edit boundary, then dispatch exactly one isolated custom agent named `code_simplifier_agent`. The agent simplifies code without changing behavior.

1. Confirm that the current context is a Git repository. Otherwise, stop and ask the user to run from a repository or provide usable project context.
2. Treat any concrete scope in the user's current request as authoritative explicit scope, whether invocation is explicit or implicit. A concrete scope names paths, files, symbols, modules, tests, changed units, or an unambiguous plain-language project region. If `$code-simplifier` appears, ignore only the skill mention and treat the remaining concrete boundary text as scope. A generic request to simplify code is not explicit scope and continues to default resolution. Inspect the repository to resolve scope, and ask only if materially different interpretations remain.
3. Without explicit scope, inspect staged, unstaged, and untracked changes. If any exist, the complete dirty set is the resolved scope. Do not inspect or select PR/MR scope for this invocation.
4. Only when the worktree is clean, establish an associated GitHub PR or GitLab MR and its base from runtime metadata, `gh pr view`, or `glab mr view`. Use the complete PR/MR diff. Do not assume a base branch. If the association, base, or diff cannot be established, stop and ask the user to provide or confirm scope.
5. Summarize the resolved boundary. For a diff, this means the changed code units plus complete untracked files. The custom agent may read adjacent code as context, but may edit only the resolved boundary.
6. Spawn exactly one isolated custom agent with custom agent type/name `code_simplifier_agent`, wait for it to finish, and return its result. Tell it to read applicable `AGENTS.md`, preserve user changes, and not commit, push, or open a PR/MR.

Use this dispatch prompt shape, filling in concrete values:

```text
Scope source: explicit | uncommitted changes | PR <identifier> | MR <identifier>
Scope: concrete paths, changed units, or plain-language boundary
Edit boundary: edit only the resolved scope; adjacent reads are context-only
Expected result: behavior-preserving simplifications, proportionate verification, and a concise summary of files, significant changes, test results, and limitations
```

The only valid workflow outputs are one successful `code_simplifier_agent` dispatch or a clear stop. If `code_simplifier_agent` is unavailable, stop. Do not substitute another agent, copy this prompt into a general agent, or simplify inline.

Team pressure and an available PR never override a dirty worktree: any staged, unstaged, or untracked changes are the complete default scope. Time pressure and a small scope never permit inline work or a substitute agent: unavailable `code_simplifier_agent` means stop.
