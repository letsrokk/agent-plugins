# Codex plugin structure and setup

Use when Codex is a declared or requested target, regardless of which client runs the audit.

## Official sources

| Question | Source |
| --- | --- |
| Package structure and native manifest fields | [Package your plugin](https://developers.openai.com/plugins/build/plugins) |
| Skill discovery and invocation | [Build skills](https://learn.chatgpt.com/docs/build-skills) |

Approved documentation domains: `developers.openai.com`, `learn.chatgpt.com`, and `platform.openai.com`. Fetch packaging guidance for structure and skill guidance for discovery or invocation. Prompt content is covered by the shared prompting reference linked from SKILL.md.

## Inspect

- Compare root and `.codex-plugin/plugin.json` definitions with the documented loading mode. Check skill routes, interface/default prompts, and declared component paths. Consult linked official component documentation for custom agents, hooks, or MCP only when present.
- Do not assume the existence of a native manifest proves that its components load alongside a portable manifest. Where documentation cannot settle a loader question, inspect the relevant revision of the official [Codex loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs) and [portable adapter](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/agent_plugin_manifest.rs). Restrict GitHub retrieval to `openai/codex`, including related definitions needed to trace that behavior. Cite the resolved commit or release; current `main` does not prove support in an older installed client.
- Review `SKILL.md`, referenced prompts, `agents/openai.yaml` when present, custom-agent definitions, and hook-injected text for their actual roles. UI metadata is not necessarily a system instruction; a skill declaration is not proof of runtime invocation.
- If client version evidence is unavailable, label version-dependent compatibility as uncertain.
