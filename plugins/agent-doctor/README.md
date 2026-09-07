# Agent Doctor

Inspect Codex and Claude Code configuration and review local session history for plugin or skill usage. Both skills are read-only: they report findings without editing configuration or history.

## Install

In the Codex CLI:

```sh
codex plugin marketplace add letsrokk/agent-plugins
codex plugin add agent-doctor@rokk-club-codex-plugins
```

In Claude Code:

```text
/plugin marketplace add letsrokk/agent-plugins
/plugin install agent-doctor@rokk-club-claude-plugins
```

## Inspect agent configuration

Ask the agent to use [inspect-agent-config](skills/inspect-agent-config/SKILL.md), for example:

```text
Use inspect-agent-config to audit this project's settings and instructions.
Use inspect-agent-config to audit my user configuration and model/effort choices.
Use inspect-agent-config with both scopes to explain which settings take precedence.
```

The skill audits the client running the task. Project scope is the default; request `user` for user scope only or `both` for user and project scope. Project-only audits do not read user files or ancestor instructions outside the project boundary.

Reports distinguish confirmed problems, provider-supported recommendations, and optional workload experiments. Each finding includes evidence, impact, and the smallest suggested edit. Missing runtime overrides, policy, trust, or account information are reported as visibility gaps.

The audit retrieves relevant approved provider documentation. It may follow one link to canonical detail needed for the audit within the provider's allowed domains, citing that derived source alongside its approved parent. It does not search or follow further links. Local paths and configuration values are never included in web requests. If approved documentation is unavailable, the skill completes the local structural audit and marks freshness unverified.

## Inspect plugin usage

Ask the agent to use [inspect-plugin-usage](skills/inspect-plugin-usage/SKILL.md) with one exact plugin or skill name:

```text
Use inspect-plugin-usage to count agent-doctor usage over the last 30 days.
Use inspect-plugin-usage to count the skill agent-doctor:inspect-agent-config.
Use inspect-plugin-usage to compare papercuts usage in this project with global usage over the last 7 days.
```

The bundled analyzer requires Python 3.11 or later. It reads local Codex and Claude session records, defaults to a 30-day window, and reports attempts, successful loads or tool invocations, direct problems, incomplete evidence, and coverage warnings. It does not return prompts or skill bodies.

To run it directly from `skills/inspect-plugin-usage/`:

```sh
python3 scripts/inspect_sessions.py --plugin agent-doctor
python3 scripts/inspect_sessions.py --skill agent-doctor:inspect-agent-config
python3 scripts/inspect_sessions.py --plugin papercuts --project /path/to/project --days 7
```

Interpret the results within these limits:

- Plugin totals count invocations of the plugin's skills, not installations or non-skill activity.
- Codex records show initial `SKILL.md` reads; a successful load requires matching frontmatter in the output and does not prove the agent applied the skill.
- Claude records use `Skill` tool calls and legacy command metadata. Legacy markers are weaker evidence and can overlap with tool results.
- Project attribution uses the session working directory and can be inaccurate when it changes during a session.
- Incomplete records are missing evidence, not confirmed failures. Coverage warnings mean totals include only readable, recognized records.

For history from before the plugin rename, query `--plugin plugin-creator` separately; historical records retain the old name.

## Development

From the plugin root, run:

```sh
python3 scripts/test.py
python3 scripts/validate.py
```

See the [repository contributor workflow](../../docs/plugin-development.md) for marketplace validation and local installation.
