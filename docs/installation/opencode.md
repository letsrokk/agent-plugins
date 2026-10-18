# OpenCode installation

OpenCode 1.19.3 on macOS discovers the core skills through explicit intact-package paths. Its native MCP connection is verified in an isolated server; policy adapters have local contract checks. The approved `opencode/big-pickle` test loaded eli5, recognized the automatic writing policy, completed a Papercuts complaint round trip, and retained the policy after native compaction. That model repeatedly encoded the requested tag array as a string; the complaint succeeded without tags, so tagged calls remain a provider-specific limitation of this run. See the [component matrix](../compatibility.md).

OpenCode's executable plugins differ from Agent Plugins packages. Keep a complete checkout; do not move `plugin.json` into `.opencode/plugins/` or copy only a skill that requires parent resources. Node.js 24+ must be on PATH for Papercuts and Copywriter generators.

## Core skills

Add these entries to your existing OpenCode configuration, replacing `/absolute/path/agent-plugins`. Merge with existing settings rather than overwriting them:

```json
{
  "skills": {
    "paths": [
      "/absolute/path/agent-plugins/plugins/eli5/skills",
      "/absolute/path/agent-plugins/plugins/code-simplifier/skills",
      "/absolute/path/agent-plugins/plugins/pr-review-toolkit/skills",
      "/absolute/path/agent-plugins/plugins/copywriter/skills"
    ]
  }
}
```

Run `opencode debug skill`. Expect 10 core skill names; built-in skills may also appear. Then explicitly request the selected workflow. Code review/simplification uses the existing local specialist fallback, not Codex TOML agent discovery.

## Optional automatic policy and Papercuts

Merge the selected entries below into the same configuration. These modules append owned policy context; they do not replace OpenCode's instructions. Encode spaces in file URLs as `%20`.

```json
{
  "plugin": [
    "file:///absolute/path/agent-plugins/plugins/read-the-room/scripts/opencode.mjs",
    "file:///absolute/path/agent-plugins/plugins/papercuts/scripts/opencode.mjs"
  ],
  "mcp": {
    "papercuts": {
      "type": "local",
      "command": ["node", "/absolute/path/agent-plugins/plugins/papercuts/dist/mcp_server.js"],
      "environment": { "PAPERCUTS_CLIENT": "opencode" },
      "enabled": true
    }
  }
}
```

Add the corresponding `plugins/read-the-room/skills` or `plugins/papercuts/skills` absolute path to `skills.paths` if you also want explicit skill discovery. Papercuts records in `~/.config/opencode/papercuts.jsonl`; its journal uses this fixed user path even if OpenCode's own configuration directory is overridden.

Restart the host after configuration changes and inspect its MCP status. The tested native server reports Papercuts connected. The system and compaction adapters use experimental OpenCode hooks; compatibility is tied to the tested API version. The tested session retained the writing policy on a second prompt and after native compaction. This is evidence for that pinned provider/host combination, not every model or lifecycle transition. Remove only the entries you added to disable these integrations.
