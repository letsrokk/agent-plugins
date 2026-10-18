# Agent installation

Use the [compatibility matrix](compatibility.md) to choose supported plugins. Keep the full checkout so sibling skills, references, generators, and bundled tools remain available. Scripted workflows require Node.js 24 or later on the agent process's `PATH`.

The root README has [Codex and Claude Code marketplace commands](../README.md#connect-your-agent). The experimental routes below use a local checkout. Replace `/absolute/path/agent-plugins` with its location and `<plugin>` with a supported plugin name.

## Copilot CLI

```sh
copilot plugin marketplace add /absolute/path/agent-plugins
copilot plugin install "<plugin>@rokk-club-copilot-plugins"
copilot plugin list
copilot skill list --json
```

Inspect each skill's `source` and `path` to confirm the intended package. Project skills take precedence over personal skills, which take precedence over plugin skills.

Papercuts and Read the Room load startup instructions through native hooks. Papercuts registers its bundled MCP server with the Copilot client identity. Inspect the effective registration with `copilot mcp get papercuts`.

Use the full installed identity with `copilot plugin disable`, `enable`, `update`, or `uninstall`. Local marketplace packages load live from the checkout; `update` keeps that route current, and `uninstall` disables the entry while retaining checkout files.

## Grok Build

```sh
grok plugin marketplace add /absolute/path/agent-plugins
grok plugin marketplace list
```

Use the source name printed by `marketplace list`. Local sources are named after their directory. For a checkout registered as `agent-plugins`, review the selected package before enabling its executable capabilities with `--trust`:

```sh
grok plugin install "<plugin>@agent-plugins" --trust
grok inspect --json
```

Invoke Read the Room and Papercuts explicitly to load their instructions. Papercuts registers its bundled MCP server with the Grok client identity; check connectivity with `grok mcp doctor`.

Use `grok plugin disable NAME`, `enable NAME`, `update NAME`, or `uninstall NAME` to manage installed packages.

## OpenCode

Merge selected entries into your existing OpenCode configuration. The following registers the four core workflow packages:

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

Run `opencode debug skill` to confirm discovery, then explicitly request a workflow.

For automatic writing and Papercuts instructions, merge the selected native extensions and MCP configuration below. Encode spaces in file URLs as `%20`.

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

Add the corresponding `plugins/read-the-room/skills` and `plugins/papercuts/skills` absolute paths to `skills.paths` for explicit skill discovery. Restart OpenCode and check its MCP status. The policy extensions append context through OpenCode's experimental system and compaction hooks.

## Pi

```sh
pi install /absolute/path/agent-plugins
pi list
```

The local package registers resources in place. It includes eli5, code-simplifier, pr-review-toolkit, copywriter, Read the Room, and Papercuts. Select skills and extensions with `pi config` and keep the checkout available.

Keep Pi's built-in MCP extension enabled for Papercuts. The package extension registers the bundled server with the Pi client identity; policy extensions refresh their owned system sections before each turn. A same-name server in native file configuration takes precedence over the packaged registration.

Start an authenticated Pi session and explicitly request a selected workflow. Use `pi remove /absolute/path/agent-plugins` to unregister the package.

See [Papercuts user storage](../plugins/papercuts/README.md#user-storage-and-migration-from-02) for each agent's journal path.
