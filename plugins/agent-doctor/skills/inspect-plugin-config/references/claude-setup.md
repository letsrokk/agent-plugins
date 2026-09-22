# Claude Code plugin structure and setup

Use when Claude Code is a declared or requested target, regardless of which client runs the audit.

## Official sources

| Question | Source |
| --- | --- |
| Manifest, layout, components, and paths | [Plugins reference](https://code.claude.com/docs/en/plugins-reference) |
| Marketplace entry for the package | [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) |
| Skill discovery, frontmatter, and invocation | [Skills](https://code.claude.com/docs/en/skills) |

Approved domains: `code.claude.com`, `platform.claude.com`, and `docs.anthropic.com`. Fetch the plugin reference for structure, the marketplace page only for an in-scope entry, and skill guidance for discovery or invocation. Follow linked component details only when relevant. Prompt content is covered by the shared prompting reference linked from SKILL.md.

## Inspect

- Check `.claude-plugin/plugin.json` when present and documented manifest-free layouts when applicable. Resolve default component discovery and explicitly declared paths using the current plugin reference. Do not assume every component belongs inside `.claude-plugin/`.
- Inspect skills, legacy commands, agents, hooks, MCP, and other declared components against their host contracts. Distinguish fields supported for plugin agents from those supported only for project or user agents. Check native `.mcp.json` separately from portable `mcp.json`.
- Check plugin-root placeholders and path resolution in launch definitions without executing them. Report environment-dependent values as unresolved where the package alone cannot establish them.
- For skill frontmatter, distinguish user invocation from model invocation and metadata from loaded instruction text. Trace referenced instructions and static hook prompts. Examples and shell substitutions in skill content must not be executed by the reviewer.
- Static package evidence does not establish enabled state, hook trust, account availability, or behavior in an unspecified client version.
