---
name: inspect-agent-config
description: Use when Codex or Claude Code configuration, instructions, model choices, effort settings, precedence, or unexpected agent behavior need a read-only audit against current official provider guidance.
---

# Inspect Agent Config

Audit the current agent client without changing its files. Separate what is provably wrong from provider guidance and optional experiments.

## Scope

Inspect the current client only: Codex when running in Codex, or Claude Code when running in Claude Code. Do not infer the client from files on disk.

- Default: project scope, rooted at the explicit project path or the current working directory.
- `user`: user scope only.
- `both`: user and project scopes.

Do not read user files for project-only requests. Resolve `~` and client-home environment variables locally. Never put local paths, configuration content, or values in a web request.

Read exactly one provider reference before inspecting files:

- Codex: [references/codex.md](references/codex.md)
- Claude Code: [references/claude.md](references/claude.md)

## Audit

1. Discover the files for the requested scope using the provider reference. Read configuration before resolving configurable instruction filenames.
2. Parse TOML or JSON locally. Report syntax errors without guessing the intended value. Redact values whose key or content resembles a credential, token, secret, password, private key, or authorization header.
3. Reconstruct precedence. Label each discovered layer as active, shadowed, ignored, or indeterminate and explain why. Do not claim an effective value when CLI flags, environment variables, trust, managed policy, account availability, or runtime state are not visible.
4. Fetch current guidance only from the exact URLs in the provider reference. Open those pages directly: do not run a general web search, follow page links, or add sources. Follow redirects only within the listed provider documentation domains. Record the retrieval date.
5. Compare the local configuration with documented keys, current model guidance, effort guidance, and instruction-file recommendations. Do not hardcode a current frontier model: derive it from the fetched pages.
6. Keep every recommendation evidence-bound. Never edit the configuration unless the user separately asks for a change.

If an approved page is unavailable, finish the local structural audit, mark freshness unverified, and omit current-model or current-recommendation claims that the available pages do not support.

## Report

Return these sections:

1. **Scope and visibility** — client, project path, requested scopes, files inspected, and unavailable runtime layers.
2. **Resolved layers** — precedence, active values, shadowed or ignored entries, and indeterminate values.
3. **Confirmed problems** — parse errors, documented invalid or obsolete settings, exposed secrets, contradictions, and load failures supported by evidence.
4. **Provider-aligned recommendations** — changes directly supported by a retrieved approved source.
5. **Optional experiments** — tuning ideas that require workload testing; state the tradeoff and how to evaluate it.
6. **Sources and freshness** — exact approved URLs used, retrieval date, unavailable pages, and resulting limits.

For instructions, call out excessive length, vague universal rules, duplicated or conflicting guidance, misplaced one-off workflows, and model-specific prompting that conflicts with the current provider guidance. Quote only the minimum local text needed to identify a problem, and never quote a secret-like value.
