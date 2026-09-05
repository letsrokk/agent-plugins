---
name: pr-review-toolkit
description: Use when a pull request or local diff needs review for bugs, test coverage, comments, error handling, or type invariants.
---

# PR Review Toolkit

Adapted from Anthropic's PR Review Toolkit for Codex. See the plugin-level `NOTICE` for source and modification details.

Resolve one review boundary and apply the relevant specialist instructions. Reviews are advisory; simplification requires an explicit user request.

## Resolve the scope

1. Prefer an explicit pull request, path, commit range, or other concrete boundary in the user's request.
2. Without explicit scope, inspect staged, unstaged, and untracked changes. If any exist, use the complete dirty set.
3. Only with a clean worktree, resolve an associated GitHub pull request with `gh pr view`. Establish its base and complete diff without assuming a base branch.
4. If no usable boundary can be established, ask for scope. Read instruction files applicable to the resolved paths.

Prepare one scope package: scope source, concrete paths and changed units, base when applicable, repository-guidance paths, and the boundary (adjacent reads are context-only). Workers must not rediscover the change boundary.

## Select and run specialists

Supported aspects are `code`, `tests`, `comments`, `errors`, `types`, `simplify`, and `all`. Run only explicitly named aspects when provided, regardless of the automatic selection conditions below. Default and `all` use those conditions to select review aspects; neither requests simplification.

- `code`: always review the resolved scope using [code reviewer](agents/pr_review_toolkit_code_reviewer.toml).
- `tests`: when meaningful production behavior or tests changed, use [test analyzer](agents/pr_review_toolkit_pr_test_analyzer.toml), including production changes without accompanying tests.
- `comments`: when comments or documentation changed, use [comment analyzer](agents/pr_review_toolkit_comment_analyzer.toml).
- `errors`: when error handling, fallbacks, retries, or failure reporting changed, use [failure hunter](agents/pr_review_toolkit_silent_failure_hunter.toml).
- `types`: when types or their invariants changed, use [type analyzer](agents/pr_review_toolkit_type_design_analyzer.toml).

Load only selected specialists' canonical instructions. For small scopes, apply them locally. Delegate substantial, independent review aspects when isolation is useful: prefer the namespaced custom agent matching the instruction filename; if unavailable, supply a general agent with that specialist's instructions and the scope package. If delegation is unavailable, review locally. Run useful independent read-only workers concurrently within host limits unless the user requests sequential execution. Avoid duplicate passes over the same concern.

Keep every review advisory: no edits, commits, pushes, posted comments, approvals, merges, or pull-request state changes.

## Report and optional simplification

Deduplicate findings by root cause and retain the strongest evidence. Lead with material findings ordered by impact, including file and line, evidence, severity, confidence, and a concrete correction. End with a brief scope, checks, and limitations summary. Omit empty sections and routine praise; if there are no material findings, say so plainly.

Severity expresses impact; confidence expresses evidence strength. Critical or high-impact findings and explicitly justified must-fix gaps block simplification. A high confidence score alone does not block it.

When the user explicitly requests `simplify`, apply the canonical [simplifier instructions](agents/pr_review_toolkit_code_simplifier.toml) within the same edit boundary after selected reviews finish without blocking findings. If only simplification was requested, proceed directly. Use the same local or delegated execution choices above, and never run edits concurrently with reviewers. Report edits, verification results, and limitations.
