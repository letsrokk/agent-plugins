# Claude Code configuration audit

Use this reference only when the current client is Claude Code.

## Discover local layers

For project scope, identify the project root and target directory. Inspect:

- Shared `.claude/settings.json` at the session's primary working directory. Resolve `.claude/settings.local.json` separately using the installed version and source 1: Git-root and worktree rules can put it in a different directory. Report locations outside the requested project without reading them.
- `CLAUDE.md`, `.claude/CLAUDE.md`, and `CLAUDE.local.md` candidates from the project root through the target directory.
- Applicable `.claude/rules/**/*.md` files, including nested rules, and instruction imports when their resolved paths are in scope. Distinguish unconditional rules from path-scoped rules loaded on demand.

Report candidates that are alternatives, excluded, unloaded, or only loaded on demand instead of assuming every discovered file is active. Within an active directory, local instructions are appended after shared instructions; closer directories are read later. In project-only mode, note that instruction files above the project root can affect the session but do not read them.

For user scope, use `${CLAUDE_CONFIG_DIR}` when set, otherwise `~/.claude`, and inspect:

- `settings.json`
- `CLAUDE.md`
- `rules/**/*.md` and in-scope instruction imports.

When visible, include managed settings, CLI flags or `--settings`, environment overrides, `/status` setting sources, `/context` memory sources, and runtime-selected model and effort. Otherwise list them as visibility gaps. Do not inspect user or managed files in project-only mode.

Settings precedence, highest first: managed; command line; project-local `.claude/settings.local.json`; shared project `.claude/settings.json`; user. Lists can merge rather than replace. Environment precedence is key-specific, so do not force environment values into that file-layer ordering.

## Approved sources

Open these pages directly. Fetch only relevant sections; reuse retrieved content. If HTML retrieval fails, try the same page's Markdown representation by appending `.md`. Do not search or follow links from these pages.

1. Settings scopes and precedence: https://code.claude.com/docs/en/settings
2. Instruction and memory discovery: https://code.claude.com/docs/en/memory
3. Model and effort configuration: https://code.claude.com/docs/en/model-config
4. Configuration troubleshooting: https://code.claude.com/docs/en/debug-your-config
5. Current model overview: https://platform.claude.com/docs/en/about-claude/models/overview
6. Prompt-engineering overview: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
7. Current prompting practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
8. Setting keys, types, and scope restrictions: https://code.claude.com/docs/en/settings-reference

Allowed redirect domains: `code.claude.com`, `platform.claude.com`, and `docs.anthropic.com` only when one of the exact pages redirects there.

For settings or precedence, fetch source 1 and source 8 for the keys under review. For instructions, fetch source 2. For model or effort advice, fetch source 3 and add source 5 for model comparisons. For prompting, use source 7; source 6 is only for deciding whether prompting addresses the problem. Fetch source 4 for ignored settings, load failures, or disputed runtime behavior. A full audit uses all applicable routes. Distinguish Claude Code model support from API availability and account access.

## Analysis boundaries

- Settings files are strict JSON. Distinguish a whole-file parse error from an invalid entry that the client can skip.
- Managed policy, flags, environment variables, account availability, and session choices can change the effective model or effort.
- Evaluate model and effort together. The documented default is the baseline; maximum effort is an experiment with cost and overthinking tradeoffs unless the workload proves a benefit.
- Prefer concise, specific instructions. Use the provider's current size guidance and recommend scoped rules for instructions that need not load in every session.
- Imports can improve organization without reducing startup context. Do not claim that splitting a file alone saves tokens.
