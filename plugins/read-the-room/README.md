# Read the Room

Help agents shape clear communication for the human and channel in front of them.

Read the Room packages a shared human-facing communication contract as one portable skill. [`skills/make-it-make-sense/SKILL.md`](skills/make-it-make-sense/SKILL.md) is the canonical policy. Channel references contain only the rules specific to each artifact.

The policy follows William Zinsser's four principles: Clarity, Simplicity, Brevity, and Humanity. It incorporates Google documentation practices and selected Simplified Technical English techniques without enforcing ASD-STE100 compliance. [Sources and adaptations](skills/make-it-make-sense/references/sources.md) records the rationale for maintainers and is not loaded at startup.

Keep startup guidance small by removing duplication and loading channel details on demand. Preserve instructions, meaningful exceptions, and writing quality before reducing size. Use the [writing scenarios](tests/writing-scenarios.md) to assess policy changes alongside the automated hook checks; those checks verify loading, not prose quality.

The `make-it-make-sense` skill covers:

- Human-readable agent updates, questions, plans, findings, blockers, and final answers
- Commit messages, pull and merge requests, reviews, and discussion replies
- Issue tracker titles, descriptions, acceptance criteria, comments, and status updates
- Wiki and knowledge-base pages, READMEs, runbooks, decision records, code comments, and durable documentation
- Chat messages, announcements, status updates, and thread replies

## Install and activate

The bundled hook requires Node.js 24 or later, with `node` available on the noninteractive host process's PATH. No npm install is needed.

### Codex

Run in a terminal:

```sh
codex plugin marketplace add letsrokk/agent-plugins
codex plugin add read-the-room@rokk-club-codex-plugins
codex plugin list
```

Confirm Read the Room is installed. In Codex, open `/hooks`, review and trust its hook, then start a fresh session. Installation alone does not trust the hook.

### Claude Code

Run inside Claude Code:

```text
/plugin marketplace add letsrokk/agent-plugins
/plugin install read-the-room@rokk-club-claude-plugins
```

Open `/plugin` and confirm Read the Room is installed and enabled, then restart Claude Code. See the [Claude Code plugin management guide](https://code.claude.com/docs/en/discover-plugins) for installation scopes and controls.

### Verify startup guidance

In a fresh session, without explicitly invoking the skill, ask:

> Summarize this result: lint and unit tests passed; integration tests received HTTP 401 instead of 200; the cause is unknown.

The response should preserve the passes, the failure, and the unknown cause. It should not invent a fix or imply all checks passed. This checks writing behavior; a good response alone does not prove the hook loaded. Check the host's hook execution information for successful loading as well. The hook displays “Loading Read the Room writing guidance...” where status messages are supported; that message alone does not establish success.

If guidance is missing, check that the plugin is enabled, the Codex hook is trusted, and `node` is available to the host. Inspect hook errors and start a fresh session after correcting the problem. If hooks are unavailable, explicitly request “Use the make-it-make-sense skill for this response.” Automatic skill discovery alone remains host-controlled.

## Update or remove

For Codex, refresh the marketplace and reinstall the plugin:

```sh
codex plugin marketplace upgrade rokk-club-codex-plugins
codex plugin add read-the-room@rokk-club-codex-plugins
```

Review the current hook definition in `/hooks` after an update and trust it if required. To uninstall, run `codex plugin remove read-the-room@rokk-club-codex-plugins`.

For Claude Code, use `/plugin` to refresh the marketplace in **Marketplaces** and manage Read the Room in **Installed**. You can update, disable, or uninstall it there. Start a fresh session after updating or removing the plugin; previously loaded guidance remains in an existing conversation.

## How startup works

In Claude Code and Codex, the `SessionStart` hook's `startup|resume|clear|compact` matcher loads the canonical policy and agent-response guide for new and resumed sessions and after context is cleared or compacted. Other channel guides remain available on demand and are reused while present in context. The hook reads the policy files on every invocation.

The hook supplies the absolute skill directory once; all guide links resolve relative to it, independently of the working directory.

See the [Codex hook documentation](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks) and [Claude Code SessionStart documentation](https://code.claude.com/docs/en/hooks#sessionstart).

For example, ask “Draft a concise pull request description” and the agent has the core writing guidance before responding, then reads the version-control guide as needed.

Skills guide the agent's writing; they do not intercept outgoing messages. Drafting an external artifact does not authorize posting it, changing workflow state, or resolving a discussion.

The root manifest retains Agent Plugins v1 metadata but omits `$schema` to select native Codex loading: Codex 0.153.4 otherwise skips hooks and ignores native MCP configuration. See the [manifest compatibility rules](../../docs/plugin-development.md#choosing-portable-or-native-loading).
