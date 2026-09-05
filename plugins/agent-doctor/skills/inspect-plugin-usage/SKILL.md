---
name: inspect-plugin-usage
description: Use when recent local Codex or Claude sessions need to be checked for a named plugin or skill's invocation counts, successful loads, direct failures, incomplete evidence, or project-specific totals.
---

# Inspect Plugin Usage

Use the bundled analyzer instead of searching session files ad hoc. It reads local history without changing it and never returns prompts or skill bodies.

Require one exact-name target:

- Use `--plugin NAME` to aggregate invocations of skills supplied by that plugin.
- Use `--skill NAME` for an exact standalone skill or fully qualified `plugin:skill` name.

Run the analyzer from this skill's directory:

```sh
python3 scripts/inspect_sessions.py --plugin NAME
python3 scripts/inspect_sessions.py --skill plugin:skill
```

Add `--project PATH` only when the user asks for a project comparison. Add `--days N` only when the user requests a window other than the default 30 days.

The rename does not rewrite session history. Query new calls with `--plugin agent-doctor`; query earlier calls separately with `--plugin plugin-creator` when the user wants pre-rename history.

Summarize the returned JSON with:

- the target and time window;
- global attempts, successful invocations, direct problems, and incomplete invocations;
- the project subtotal when present;
- the Codex and Claude breakdown;
- problem categories and coverage warnings.

State these limits every time:

- Plugin totals cover invocations of skills supplied by that plugin, not plugin installation or non-skill activity.
- Codex calls are inferred from recognized initial `SKILL.md` reads; Claude calls use recognized `Skill` tool records and legacy command markers.
- Project attribution uses the session working directory and can be inaccurate when a session changes directories.
- A legacy Claude command marker is weaker evidence than a completed `Skill` tool result and can overlap with one.

Treat `incomplete` as missing evidence, not a confirmed failure. Treat problem categories as direct load or tool-result evidence, not proof that the skill later behaved incorrectly. Suggest troubleshooting only when the returned category or warning supports it, and label other possible causes as unverified. Never quote transcript content. If coverage warnings exist, explain that counts reflect only readable, recognized session records.
