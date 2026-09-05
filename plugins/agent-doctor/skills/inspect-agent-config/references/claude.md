# Claude Code configuration audit

Use this reference only when the current client is Claude Code.

## Discover local layers

For project scope, identify the project root and target directory. Inspect:

- `.claude/settings.json` and `.claude/settings.local.json` at the applicable project location.
- `CLAUDE.md`, `.claude/CLAUDE.md`, and `CLAUDE.local.md` candidates from the project root through the target directory.
- Applicable `.claude/rules/*.md` files and instruction imports when their paths are in scope.

Report candidates that are alternatives, excluded, unloaded, or only loaded on demand instead of assuming every discovered file is active. Within an active directory, local instructions are appended after shared instructions; closer directories are read later. In project-only mode, note that instruction files above the project root can affect the session but do not read them.

For user scope, use `${CLAUDE_CONFIG_DIR}` when set, otherwise `~/.claude`, and inspect:

- `settings.json`
- `CLAUDE.md`

When visible, include managed settings, CLI flags or `--settings`, environment overrides, `/status` setting sources, `/context` memory sources, and runtime-selected model and effort. Otherwise list them as visibility gaps. Do not inspect user or managed files in project-only mode.

Settings precedence, highest first: managed; command line; project-local `.claude/settings.local.json`; shared project `.claude/settings.json`; user. Lists can merge rather than replace. Environment precedence is key-specific, so do not force environment values into that file-layer ordering.

## Approved sources

Open these exact pages directly. Do not search or follow links from them.

1. Settings scopes and precedence: https://code.claude.com/docs/en/settings
2. Instruction and memory discovery: https://code.claude.com/docs/en/memory
3. Model and effort configuration: https://code.claude.com/docs/en/model-config
4. Configuration troubleshooting: https://code.claude.com/docs/en/debug-your-config
5. Current model overview: https://platform.claude.com/docs/en/about-claude/models/overview
6. Prompt-engineering overview: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
7. Current prompting practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

Allowed redirect domains: `code.claude.com`, `platform.claude.com`, and `docs.anthropic.com` only when one of the exact pages redirects there.

Fetch sources 1, 2, 3, 5, 6, and 7 for a complete audit. Fetch source 4 only when a file failed to load, a setting appears ignored, precedence is disputed, or runtime behavior conflicts with the files. Identify current models and effort support from the fetched pages; never rely on model names remembered by the agent or stored in this skill.

## Analysis boundaries

- Settings files are strict JSON. Distinguish a whole-file parse error from an invalid entry that the client can skip.
- Managed policy, flags, environment variables, account availability, and session choices can change the effective model or effort.
- Evaluate model and effort together. The documented default is the baseline; maximum effort is an experiment with cost and overthinking tradeoffs unless the workload proves a benefit.
- Prefer concise, specific instructions. Use the provider's current size guidance and recommend scoped rules for instructions that need not load in every session.
- Imports can improve organization without reducing startup context. Do not claim that splitting a file alone saves tokens.
