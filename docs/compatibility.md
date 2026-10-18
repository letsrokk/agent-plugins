# Plugin compatibility matrix

Use this matrix to choose plugins and installation routes for your coding harness. Copilot CLI, Grok Build, OpenCode, and Pi support is experimental.

## Supported plugins

A checkmark identifies a supported plugin and harness combination. Follow the installation guide for its activation steps.

| Plugin | Codex | Claude Code | Copilot CLI | Grok Build | OpenCode | Pi |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| [eli5](../plugins/eli5/README.md) | ✓ | | ✓ | ✓ | ✓ | ✓ |
| [code-simplifier](../plugins/code-simplifier/README.md) | ✓ | | ✓ | ✓ | ✓ | ✓ |
| [pr-review-toolkit](../plugins/pr-review-toolkit/README.md) | ✓ | | ✓ | ✓ | ✓ | ✓ |
| [copywriter](../plugins/copywriter/README.md) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| [read-the-room](../plugins/read-the-room/README.md) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| [papercuts](../plugins/papercuts/README.md) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| [agent-doctor](../plugins/agent-doctor/README.md) | ✓ | ✓ | | | | |

Install complete `plugins/<name>/` packages so sibling skills, references, generators, and bundled tools stay available. Scripted workflows require Node.js 24 or later on the harness process's `PATH`.

## Installation and policy activation

Read the Room supplies writing guidance; Papercuts supplies workflow-friction guidance and tools through the Model Context Protocol (MCP).

| Harness | Installation | Read the Room and Papercuts policy activation | Papercuts tools |
| --- | --- | --- | --- |
| Codex | [Native marketplace](../README.md#marketplaces) | Startup hooks; review and trust in `/hooks`, then start a fresh session | Native MCP |
| Claude Code | [Native marketplace](../README.md#marketplaces) | Startup hooks | Native MCP |
| Copilot CLI | [Native marketplace](installation/copilot.md) | Startup hooks | Native MCP |
| Grok Build | [Native marketplace](installation/grok.md) | Explicit skill invocation | Native MCP |
| OpenCode | [Skill paths and native configuration](installation/opencode.md) | System and compaction hooks | Native MCP |
| Pi | [Local package](installation/pi.md) | Before-turn system sections | Native MCP |

Papercuts stores records in a fixed user journal for each harness:

| Harness | Journal |
| --- | --- |
| Codex | `~/.codex/papercuts.jsonl` |
| Claude Code | `~/.claude/papercuts.jsonl` |
| Copilot CLI | `~/.copilot/papercuts.jsonl` |
| Grok Build | `~/.grok/papercuts.jsonl` |
| OpenCode | `~/.config/opencode/papercuts.jsonl` |
| Pi | `~/.pi/agent/papercuts.jsonl` |

## Tested versions

Compatibility checks ran on macOS with Node.js 26.12.0 on 2026-10-18. The [verification record](plans/2026-10-18-multi-harness-progress.md) contains detailed package, runtime, and model evidence.

| Harness | Version | Observed integration checks |
| --- | --- | --- |
| Codex | 0.163.0 | Marketplace registration; Papercuts and Read the Room installation and activation |
| Claude Code | 2.1.268 | Packaged Papercuts MCP connection and Claude client selection; relocated shared-hook checks |
| Copilot CLI | 1.0.98 | Six packages and 12 skills; install/update/enable/disable/uninstall; skill precedence; eli5 invocation; startup policy; tagged Papercuts round trip; session resume and manual compaction |
| Grok Build | 1.0.62 (`1474f9cbdd91`) | Six packages and 12 skills; install/update/enable/disable/uninstall; eli5 and explicit policy invocation; tagged Papercuts round trip |
| OpenCode | 1.19.3 | Core skill discovery; eli5 invocation; automatic policy; Papercuts round trip; session resume and compaction with `opencode/big-pickle` |
| Pi | 1.3.0 | Package/resource loading; eli5 invocation; outbound policy delivery; tagged Papercuts round trip; compaction and disk-backed resume with `openai-codex/gpt-6.1-sol` |
