# Claude prompting review

Shared by agent-configuration and plugin-configuration audits. Read when reviewing Claude instructions or prompts, not for settings or package structure alone. Follow the invoking skill's scope and source-retrieval rules.

## Official sources

- [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): current prompting advice. Apply each recommendation only to the models and features it addresses.
- [Prompt-engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview): fetch only when deciding whether prompting addresses the reported problem.
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): fetch when reviewing skill descriptions, instruction design, or supporting references.

Approved domains: `code.claude.com`, `platform.claude.com`, and `docs.anthropic.com`. Fetch only sources relevant to the question, reuse retrieved pages, and record retrieval dates. If sources are unavailable, disclose the freshness gap rather than presenting remembered advice as current.

## Review guidance

- Prefer concise, task-specific instructions. Identify concrete conflicts, duplication, vague universal rules, misplaced one-off workflows, and outdated model-specific guidance while preserving deliberate constraints.
- Use current size guidance in its intended context. Recommend scoped instructions when they need not load for every task. Imports can improve organization without reducing startup context; splitting a file alone does not establish a token saving.
- For skills, evaluate meaningful descriptions, reference depth, and the amount of context loaded for the task. Treat authoring recommendations as guidance unless the host defines a hard requirement; do not insist on examples, XML tags, or a fixed template for every prompt.
- Preserve explicit model choices. If no model is established, use general guidance and label model-specific recommendations as conditional. API guidance does not establish Claude Code feature support, account access, or runtime effectiveness.

Source discovery and instruction loading belong to the invoking skill's configuration or plugin setup references. This reference evaluates the content after that scope is established.
