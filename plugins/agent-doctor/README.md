# Agent Doctor

Inspect agent settings, plugin structure and prompts, and plugin and skill usage in local Codex and Claude Code sessions.

```text
$inspect-agent-config audit this project's settings and instructions
$inspect-plugin-config audit plugins/my-plugin for structure and prompt issues
$inspect-plugin-usage how often was papercuts used in the last 30 days
```

Reports configuration problems, suggested fixes, and observed skill usage from local sessions without changing your files.

Plugin configuration audits cover declared Codex and Claude Code targets and open-standard conformance where claimed, using current official sources. You can narrow an audit to structure, prompts, or one client. The audit does not execute the plugin or inspect installation state.

The plugin-usage inspection script requires Node.js 24 LTS and uses only built-in modules. Configuration inspection does not require Node.js.

## Other harnesses

Current settings and usage inspection covers Codex and Claude Code. Running the skills in another harness does not add support for that harness’s settings or session format. Portable package inspection can still review an explicitly selected package against its declared targets; see the [compatibility matrix](../../docs/compatibility.md).
