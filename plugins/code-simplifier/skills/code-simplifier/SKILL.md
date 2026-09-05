---
name: code-simplifier
description: Use when the user asks to simplify or refactor existing code for clarity while preserving behavior, within specified files, local changes, or a PR/MR.
---

# Code Simplifier

Adapted from Anthropic's Code Simplifier plugin for Codex. See the plugin-level `NOTICE` for source and modification details.

Resolve one edit boundary, then apply the canonical [simplifier instructions](agents/code_simplifier_agent.toml).

1. Prefer concrete scope in the user's request: paths, symbols, modules, changed units, or an unambiguous project region. Inspect the project to locate it; ask only when materially different interpretations remain.
2. Without explicit scope, inspect staged, unstaged, and untracked changes in the Git repository. If any exist, use the complete dirty set; do not substitute a hosted PR/MR.
3. Only with a clean worktree, establish an associated GitHub PR or GitLab MR and its base from runtime metadata, `gh pr view`, or `glab mr view`. Use the complete diff without assuming a base branch. If no usable boundary can be established, ask for scope.
4. Summarize the edit boundary: explicit scope, or changed code units plus complete untracked files. Adjacent reads are context-only.

For a small, clear scope, read the canonical agent instructions and simplify inline. For complex work that benefits from isolation, prefer one `code_simplifier_agent` custom agent. If named dispatch is unavailable, give a general agent only the canonical instructions and the scope package below. If delegation is unavailable, apply those instructions locally.

Provide delegated work with the scope source, concrete paths and changed units, base when applicable, applicable repository-guidance paths, and the hard edit boundary. The worker must not rediscover the scope. Wait for its result, then report significant changes, verification results, and limitations.
