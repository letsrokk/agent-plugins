# Pi installation

Pi 1.3.0 on macOS installs this checkout as a local package and discovers its explicit resources. The native extension runner prepares both policy sections without replacing host instructions; native MCP tools completed an isolated complaint round trip. A real `openai-codex/gpt-6.1-sol` session also invoked eli5, completed a tagged Papercuts round trip, and retained policy after native compaction. See the [component matrix](../compatibility.md).

Keep a complete checkout with Node.js 24+ on PATH. Pi's package metadata is the root `package.json` `pi` field, not the Codex or Claude marketplaces.

1. Install the local checkout:

   ```sh
   pi install /absolute/path/agent-plugins
   pi list
   ```

   Local installation registers resources in place without copying them or installing contributor dependencies. Keep the checkout intact. The package selects four core workflow packages, Read the Room, and Papercuts. It does not install Agent Doctor or Codex-specific specialist agents.

2. Review/select resources with `pi config`. The package includes Read the Room and Papercuts policy extensions; disable their extension resources if you want only core skills. Keep Pi's built-in MCP extension enabled when using Papercuts.

3. Start Pi and explicitly request a selected core workflow. Verify that its required resources load; a package listing alone does not establish workflow behavior.

## Native policy and tools

Policy extensions refresh only their owned system-prompt sections at `before_agent_start`, preserving other instructions. Papercuts registers the committed server through Pi's native `registerMcpServer` API with direct tool exposure and explicit `PAPERCUTS_CLIENT=pi`. No third-party MCP bridge is needed. A same-name server in native file configuration takes precedence, so inspect that configuration if an expected packaged server is absent.

Papercuts uses `~/.pi/agent/papercuts.jsonl`. The tested Pi runtime exposed nine MCP tools and completed lodge/list/inspect operations through them in an isolated home. Outbound request payloads contained both canonical policies before the first response, across a second prompt, and after native compaction. The test reused an existing Codex access token in an in-memory OAuth credential store; it did not save another credential cache or refresh the shared token. Interactive Pi sign-in remains the installation route for normal use.

No native subagent orchestration is required: code-simplifier and PR Review Toolkit use their local fallback. An optional upstream subagent extension is not treated as a core dependency.

Use `pi remove /absolute/path/agent-plugins` to unregister the local package. Pi's Git package installation has different dependency-install behavior at the cloned repository root; it was source-reviewed but was not the local route verified here. `package.json` remains `private: true`; this integration does not publish an npm package.
