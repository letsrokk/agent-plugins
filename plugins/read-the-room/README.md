# Read the Room

Help agents shape clear communication for the human and channel in front of them.

Read the Room packages a shared human-facing communication contract as one portable skill. [`skills/make-it-make-sense/SKILL.md`](skills/make-it-make-sense/SKILL.md) is the canonical policy. Channel references contain only the rules specific to each artifact.

The `make-it-make-sense` skill covers:

- Human-readable agent updates, questions, plans, findings, blockers, and final answers
- Commit messages, pull and merge requests, reviews, and discussion replies
- Issue tracker titles, descriptions, acceptance criteria, comments, and status updates
- Wiki and knowledge-base pages, READMEs, runbooks, decision records, code comments, and durable documentation
- Chat messages, announcements, status updates, and thread replies

The bundled `SessionStart` hook requires Node.js 24 LTS or later, with `node` available on the noninteractive host process’s PATH. No npm install is needed. In Claude Code and Codex, it loads the canonical policy and agent-response guide when a session starts, resumes, clears, or compacts. Other channel guides remain available on demand and are reused while present in context. The hook reads the policy files on every invocation.

In Codex, review and trust the plugin hook through `/hooks` before it can run. Installing the plugin alone does not trust its hooks. After installing or updating, review the current definition and start a fresh session without explicitly invoking the skill. The hook displays “Loading Read the Room writing guidance...” where the host supports status messages. In Claude Code, restart after installation and verify the same fresh-session behavior. See the [Codex hook documentation](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks) and [Claude Code SessionStart documentation](https://code.claude.com/docs/en/hooks#sessionstart).

For example, ask “Draft a concise pull request description” and the agent has the core writing guidance before responding, then reads the version-control guide as needed. If hooks are disabled or unavailable, invoke `make-it-make-sense` explicitly, or require it in host-level instructions. Automatic skill discovery alone remains host-controlled.

Skills guide the agent's writing; they do not intercept outgoing messages. Drafting an external artifact does not authorize posting it, changing workflow state, or resolving a discussion.

The root manifest retains Agent Plugins v1 metadata but omits `$schema` to select native Codex loading: Codex 0.153.4 otherwise skips hooks and ignores native MCP configuration. See the [manifest compatibility rules](../../docs/plugin-development.md#choosing-portable-or-native-loading).
