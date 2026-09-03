---
name: pr-review-toolkit
description: Use when a pull request or local change set needs focused or comprehensive review for code quality, tests, comments, error handling, type design, or behavior-preserving simplification.
---

# PR Review Toolkit

Adapted from Anthropic's PR Review Toolkit for Codex. See the plugin-level `NOTICE` for source and modification details.

Resolve one review boundary, select the requested or applicable specialists, dispatch the namespaced custom agents, and aggregate their results. Preserve the upstream behavior that simplification runs only after review passes or when the user explicitly requests `simplify`.

## Resolve the scope

1. Confirm that the current context is a Git repository. Otherwise, stop and ask the user to run from a repository or provide usable project context.
2. Parse any requested aspects: `comments`, `tests`, `errors`, `types`, `code`, `simplify`, or `all`. Treat `parallel` as an execution preference, not a review aspect. Reject unknown aspect names with the supported list.
3. Prefer an explicit pull request, path, commit range, or other concrete boundary in the user's request.
4. Without explicit scope, inspect staged, unstaged, and untracked changes. If any exist, use the complete dirty set and do not substitute a hosted pull request.
5. Only when the worktree is clean, resolve an associated GitHub pull request with `gh pr view`. Establish its base and use the complete diff. Do not assume a base branch.
6. If no usable boundary can be established, stop and ask the user to provide or confirm one.
7. Read all instruction files that apply to the resolved paths, including `AGENTS.md` and client-equivalent repository guidance.

Prepare one scope package for every dispatched agent:

```text
Scope source: explicit | uncommitted changes | PR <identifier>
Scope: concrete paths and changed units
Base: base commit or branch when applicable
Instructions: applicable repository-guidance paths
Boundary: review only this scope; adjacent reads are context-only
Expected result: the specialist's required structured report with file and line evidence
```

Do not ask agents to rediscover the pull request or change boundary independently.

## Select reviewers

When the user names aspects, run exactly those specialists. `all` means all specialists applicable to the resolved change set, followed by simplification when review passes. Without named aspects, use the same behavior as `all`:

- `code`: always run `pr_review_toolkit_code_reviewer`.
- `tests`: run `pr_review_toolkit_pr_test_analyzer` when tests changed.
- `comments`: run `pr_review_toolkit_comment_analyzer` when comments or documentation changed.
- `errors`: run `pr_review_toolkit_silent_failure_hunter` when error handling, fallbacks, retries, or failure reporting changed.
- `types`: run `pr_review_toolkit_type_design_analyzer` when types or their invariants changed.
- `simplify`: run `pr_review_toolkit_code_simplifier` only after the selected reviewers report no blocking findings. When `simplify` is the only explicitly requested aspect, dispatch it directly.

Dispatch each reviewer as an isolated custom agent with the prepared scope package. If the user requests parallel execution, dispatch independent read-only reviewers concurrently within the available agent limit. Otherwise, dispatch them sequentially. The simplifier always waits for the review result and never runs in parallel with reviewers.

Tell each reviewer to remain advisory, make no edits, preserve user work, and not commit, push, post comments, approve, merge, or change pull-request state. If a required custom agent is unavailable, stop rather than performing that specialist review inline or substituting another agent.

## Aggregate and simplify

Deduplicate overlapping findings by root cause and keep the strongest evidence. Organize the combined result as:

```markdown
# PR Review Summary

## Critical Issues
## Important Issues
## Suggestions
## Strengths
## Recommended Action
```

Treat findings labeled critical, high, important, must-fix, test criticality 5-10, or code-review confidence 80-100 as blocking. Do not run the simplifier while blocking findings remain. Report the action plan and let the user address them before a new review.

When simplification runs, give `pr_review_toolkit_code_simplifier` the same resolved edit boundary. Require behavior preservation, protection of all existing user changes, proportionate verification, and a concise report of edits and test results. It must not commit, push, or open or update a pull request.
