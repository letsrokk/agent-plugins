---
name: inspect-plugin-usage
description: Inspect recent local Codex and Claude sessions for exact plugin or skill invocation counts, successful loads, direct failures, and project-specific totals. Use when someone asks how often a plugin or skill was used or whether its invocation encountered problems.
---

# Inspect Plugin Usage

Use the bundled analyzer instead of searching session files ad hoc. It reads local history without changing it and never returns prompts or skill bodies.

Require one exact target:

- Use `--plugin NAME` to aggregate invocations of skills supplied by that plugin.
- Use `--skill NAME` for an exact standalone skill or fully qualified `plugin:skill` name.

Run the analyzer from this skill's directory:

```sh
python3 scripts/inspect_sessions.py --plugin NAME
python3 scripts/inspect_sessions.py --skill plugin:skill
```

Add `--project PATH` only when the user asks for a project comparison. Add `--days N` only when the user requests a window other than the default 30 days.

Summarize the returned JSON with:

- the target and time window;
- global attempts, successful invocations, direct problems, and incomplete invocations;
- the project subtotal when present;
- the Codex and Claude breakdown;
- problem categories and coverage warnings.

State that plugin totals cover skill invocations only. Treat `incomplete` as missing evidence, not a confirmed failure. If coverage warnings exist, explain that the counts reflect readable, recognized session records.
