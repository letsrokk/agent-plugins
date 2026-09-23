# Claude blog guidance

Use https://claude.dev/blog/ as a supplemental source for Claude harness setup and model-specific prompting advice. Load this reference only when the audit needs those topics; skip it for package structure alone.

## Discovery

Open a relevant known article directly. To find newer or more specific guidance, search only `site:claude.dev/blog/` using public model or generation names and the topic under review, such as `Claude Code context configuration` or `Opus prompting`. Never include local paths, configuration content, or private task details. Fetch the article before relying on it; search snippets are not evidence. Keep blog retrieval and redirects within `claude.dev`; use the invoking reference's approved documentation sources for corroboration.

Starting points, subject to retrieval and applicability checks:

- [The new rules of context engineering for Claude 5 generation models](https://claude.dev/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models/)
- [Getting the most out of Opus 5.5](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/)

## Filter by claim

- **Agent configuration:** use sections about the coding-agent harness, context management, tools, model/effort settings, and instruction loading only when they apply to the inspected client and version. Verify setting names, precedence, and feature support against current client documentation. Custom API harness advice does not establish Claude Code behavior.
- **Plugin and prompt review:** use sections about prompt wording, skill instructions, task framing, and model-specific behavior. Apply only to the selected Claude target and relevant model or generation. Harness setup advice belongs in an agent-configuration audit, not a plugin prompt finding.
- A mixed article can support both routes; select individual claims rather than treating the whole article as applicable. Skip unrelated release news, benchmarks, and setup tricks outside the audit scope. If the model is unknown, keep model-specific advice conditional.

Record the article URL, publication/update date when available, retrieval date, and applicable model/client. Check for superseding guidance. Treat blog advice as supplemental, not a configuration or manifest contract; distinguish verified provider advice from third-party suggestions and workload experiments. Resolve conflicts using current documentation for the same model and client, and disclose unresolved differences. If retrieval fails, mark freshness unverified and make no claims from the title or remembered content.
