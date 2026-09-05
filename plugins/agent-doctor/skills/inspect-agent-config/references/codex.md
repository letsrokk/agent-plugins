# Codex configuration audit

Use this reference only when the current client is Codex.

## Discover local layers

For project scope, identify the project root (normally the Git root) and target directory. Inspect from the root down to the target:

- `.codex/config.toml` in each directory; project layers apply only when the project is trusted.
- One instruction file per directory: `AGENTS.override.md`, otherwise `AGENTS.md`, otherwise the first configured `project_doc_fallback_filenames` match.

Read applicable configuration first because `project_doc_fallback_filenames` and `project_doc_max_bytes` change instruction discovery. Note empty, shadowed, and truncated instruction files. A closer instruction file is appended later; it does not erase unrelated parent guidance.

For user scope, use `${CODEX_HOME}` when set, otherwise `~/.codex`, and inspect:

- `config.toml`
- `AGENTS.override.md` when non-empty, otherwise `AGENTS.md`; report the unused file as shadowed when both exist.

When visible, include selected profile configuration, CLI `--config` values, environment overrides, system configuration, trust state, and managed requirements. Otherwise list them as visibility gaps. Do not inspect user or system layers in project-only mode.

Configuration precedence, highest first: CLI flags and `--config`; project `.codex/config.toml` from root to target with the closest winning; selected profile; user config; system config; defaults.

## Approved sources

Open these exact pages directly. Do not search or follow links from them.

1. Config basics and precedence: https://learn.chatgpt.com/docs/config-file/config-basic
2. Config keys and status: https://learn.chatgpt.com/docs/config-file/config-reference
3. Instruction discovery: https://learn.chatgpt.com/docs/agent-configuration/agents-md
4. Current frontier-model guidance: https://developers.openai.com/api/docs/guides/latest-model

Allowed redirect domains: `learn.chatgpt.com`, `developers.openai.com`, and `platform.openai.com` only when one of the exact pages redirects there.

Fetch all four pages for a complete audit. Use the current-model page to identify the current recommended model and migration advice at audit time; never rely on a model name remembered by the agent or stored in this skill. Use the config reference to validate key names, accepted values, deprecations, and model/effort controls.

## Analysis boundaries

- A setting inside an untrusted project layer may be ignored; do not treat that same layer as proof of trust.
- A model or effort value can be syntactically valid but unavailable to the account or overridden for the session.
- Evaluate model and effort together. Provider defaults are the baseline; higher effort is an experiment unless current guidance makes it necessary for the workload.
- Current frontier models can be more sensitive to instructions. Flag conflicting, redundant, universal, or outdated model-specific guidance, but preserve durable project constraints.
