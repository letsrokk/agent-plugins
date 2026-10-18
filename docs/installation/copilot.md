# Copilot CLI installation

The local marketplace route was checked with Copilot CLI 1.0.98 on macOS. Installation/discovery is verified for all six catalog packages; an eli5 model invocation and a native Papercuts round trip also pass. See the [component matrix](../compatibility.md) before relying on automatic instructions or tools. VS Code Local and VS Code Copilot are excluded from this iteration.

Use a complete checkout containing these catalog changes. Until this implementation is released, check out its implementation revision rather than assuming the remote default branch contains it. Node.js 24+ must be on the client process's PATH for scripted workflows.

1. Register the local checkout, replacing the example path:

   ```sh
   copilot plugin marketplace add /absolute/path/agent-plugins
   ```

2. Install a selected core package:

   ```sh
   copilot plugin install eli5@rokk-club-copilot-plugins
   ```

   The other core package names are `code-simplifier`, `pr-review-toolkit`, and `copywriter`.

3. Check the selected package and its skills:

   ```sh
   copilot plugin list
   copilot skill list --json
   ```

   Expect the package and its skill descriptions. Inspect each active skill’s `source` and `path`; they should point to the intended plugin. Copilot CLI 1.0.98 selects a same-name project skill ahead of a personal skill, and a personal skill ahead of the plugin. Removing those overrides restores the plugin source. Copywriter has seven skills. Local marketplace packages are loaded live from the checkout, so retain its complete directory structure. The tested CLI warns that direct plugin installs are deprecated; use the marketplace route.

4. In an authenticated session, explicitly request the selected workflow, for example: “Use eli5 to explain a stack in plain text.” Listing alone does not prove this step.

## Policy and tools

Papercuts and Read the Room provide native `.plugin/plugin.json` hook metadata and a Copilot startup result envelope. They retain schema-free root manifests so the native hook route is selected. Papercuts' native manifest selects `.mcp.json`, which launches its committed bundle with explicit `PAPERCUTS_CLIENT=copilot`; records select `~/.copilot/papercuts.jsonl`.

A signed-in first response loaded eli5 and recognized the automatic writing policy. A resumed second prompt used native MCP tools to inspect storage and lodge/list one tagged complaint in the correct client journal. Native manual `/compact` completed successfully; the following response retained the writing-policy title and correct journal path, with Papercuts execution denied. Use `copilot mcp get papercuts` to inspect effective server registration; it does not prove a tool round trip.

Use the full installed identity, such as `eli5@rokk-club-copilot-plugins`, with `copilot plugin disable`, `enable`, `update`, or `uninstall`. All four operations were checked for each catalog package. For this local marketplace route, `update` reports that the package is already loaded live; `uninstall` disables the entry and leaves the checkout files intact. Disabled entries remain listed, but their skills disappear from discovery. Check the CLI's own help if its version differs from the tested release.
