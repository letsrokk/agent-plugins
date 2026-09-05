# Codex configuration audit

Use this reference only when the current client is Codex.

## Discover local layers

For project scope, identify the project root (normally the Git root) and target directory. Inspect from the root down to the target:

- `.codex/config.toml` in each directory; project layers apply only when the project is trusted.
- The first non-empty instruction file per directory: `AGENTS.override.md`, then `AGENTS.md`, then configured `project_doc_fallback_filenames` in order.

Read applicable configuration first because `project_doc_fallback_filenames` and `project_doc_max_bytes` change instruction discovery. Note empty, shadowed, and truncated instruction files. A closer instruction file is appended later; it does not erase unrelated parent guidance.

For user scope, use `${CODEX_HOME}` when set, otherwise `~/.codex`, and inspect:

- `config.toml`
- The selected profile file when its selection is visible; use the fetched configuration guidance to resolve its location and format for the installed version.
- `AGENTS.override.md` when non-empty, otherwise `AGENTS.md`; report the unused file as shadowed when both exist.

When visible, include selected profile configuration, CLI `--config` values, environment overrides, system configuration, trust state, and managed requirements. Otherwise list them as visibility gaps. Do not inspect user or system layers in project-only mode.

Configuration precedence, highest first: CLI flags and `--config`; project `.codex/config.toml` from root to target with the closest winning; selected profile; user config; system config; defaults.

## Approved sources

Open these pages directly. Fetch only relevant sections; reuse retrieved content. If HTML retrieval fails, try the same page's Markdown representation by appending `.md`. Do not search or follow links from these pages.

1. Config basics and precedence: https://learn.chatgpt.com/docs/config-file/config-basic
2. Config keys and status: https://learn.chatgpt.com/docs/config-file/config-reference
3. Instruction discovery: https://learn.chatgpt.com/docs/agent-configuration/agents-md
4. Agent model availability and selection: https://learn.chatgpt.com/docs/models
5. Model prompting and migration guidance: https://developers.openai.com/api/docs/guides/latest-model

Allowed redirect domains: `learn.chatgpt.com`, `developers.openai.com`, and `platform.openai.com` only when one of the exact pages redirects there.

For settings or precedence, fetch sources 1 and 2. For instruction discovery, add source 3. For model or effort recommendations, add source 4; fetch source 5 only for model-specific prompting or migration advice. A full audit uses all applicable routes. API model guidance does not prove agent-client or account availability, and a newer model alone does not make an existing selection invalid.

## Analysis boundaries

- A setting inside an untrusted project layer may be ignored; do not treat that same layer as proof of trust.
- Check key-specific scope restrictions in source 2 before applying the general precedence order; some keys are ignored in project configuration even when trusted.
- A model or effort value can be syntactically valid but unavailable to the account or overridden for the session.
- Evaluate model and effort together. Provider defaults are the baseline; higher effort is an experiment unless current guidance makes it necessary for the workload.
- Current frontier models can be more sensitive to instructions. Flag conflicting, redundant, universal, or outdated model-specific guidance, but preserve durable project constraints.
