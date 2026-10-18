# Plugin compatibility matrix

Use this matrix to choose plugins for your coding harness. Copilot CLI, Grok Build, OpenCode, and Pi support is experimental.

## Supported plugins

A checkmark identifies a supported plugin and harness combination. See each plugin’s README for setup.

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
