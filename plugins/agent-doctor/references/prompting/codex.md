# Codex prompting review

Shared by agent-configuration and plugin-configuration audits. Read when reviewing Codex instructions or prompts, not for settings or package structure alone. Follow the invoking skill's scope and source-retrieval rules.

## Official sources

- [Current model guidance](https://developers.openai.com/api/docs/guides/latest-model): general and model-specific prompting or migration advice. Preserve the requested model; do not substitute the newest model's guidance for it.
- [Build plugin skills](https://developers.openai.com/plugins/build/skills): fetch when reviewing skill descriptions, instruction design, or supporting references.
- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): supplemental model-specific skill design discussion. Fetch only when applicable; check whether newer official guidance supersedes it.

Approved domains: `developers.openai.com`, `learn.chatgpt.com`, and `platform.openai.com`. Fetch only sources relevant to the question, reuse retrieved pages, and record retrieval dates. If sources are unavailable, disclose the freshness gap rather than presenting remembered advice as current.

## Review guidance

- Identify conflicting, redundant, vague universal, or outdated model-specific instructions and unnecessary forced workflows. Preserve durable project constraints and the intended task; suggest concrete changes rather than treating length alone as a defect without an applicable limit or consequence.
- For skills, review whether descriptions select the intended task, conditional guidance stays conditional, and references load when needed. A reference split does not reduce context when every file remains a mandatory read.
- Distinguish discovery metadata, default prompts, always-loaded instructions, and on-demand guidance. Evaluate interactions only among instructions that can load together; a skill declaration does not prove invocation.
- Apply advice to the models it addresses. If no model is established, use general guidance and label model-specific recommendations as conditional. API guidance does not establish Codex feature support, account access, or the model used in a future invocation.

Source discovery and instruction loading belong to the invoking skill's configuration or plugin setup references. This reference evaluates the content after that scope is established.
