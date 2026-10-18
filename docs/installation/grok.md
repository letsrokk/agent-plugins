# Grok Build installation

This route targets xAI's official Grok Build, checked with CLI 1.0.62 on macOS. It does not describe arbitrary clients using a Grok model. All six catalog packages install and expose 12 skills; Papercuts' native MCP handshake is verified; eli5 model invocation and a corrected native Papercuts lodge/list round trip also pass. See the [component matrix](../compatibility.md).

Use an intact checkout containing these catalog changes and Node.js 24+ for scripted workflows. Retain the checkout for local marketplace use. No npm installation is needed inside an installed plugin.

1. Register the local checkout:

   ```sh
   grok plugin marketplace add /absolute/path/agent-plugins
   grok plugin marketplace list
   ```

2. Use the registered source name printed by `marketplace list` when installing. For a checkout registered as `agent-plugins`:

   ```sh
   grok plugin install eli5@agent-plugins --trust
   ```

   The tested release names local marketplace registrations after their directory, not the catalog's `name`. Substitute the actual registered source name if different. `--trust` deliberately enables the selected plugin's executable capabilities after review; this is required by Grok's installer.

3. Inspect the installed package and actual discovered components:

   ```sh
   grok plugin details eli5
   grok inspect --json
   ```

   Expect the plugin's skill to appear. Other core packages are `code-simplifier`, `pr-review-toolkit`, and `copywriter`; Copywriter contributes seven skills. Specialist instructions run locally when no native agent definition exists.

4. In a signed-in session, invoke the workflow explicitly. This authenticated step is not established by the inspection output.

## Papercuts and writing policy

Papercuts' selected root manifest points to `.grok-plugin/mcp.json`, which launches the committed server with explicit `PAPERCUTS_CLIENT=grok` and selects `~/.grok/papercuts.jsonl`. Grok substitutes plugin-root tokens but does not export those identity markers to this MCP child; relying on them sent an early test to the standalone Codex journal. The corrected native round trip uses the Grok journal and leaves the earlier journal unchanged. `grok mcp doctor` successfully started the tested packaged server, completed its handshake, and discovered nine tools. In this release, `grok mcp list` does not show the same plugin-server inventory as `doctor`, so use the latter for connectivity.

Grok's passive startup hooks ignore stdout. Papercuts and Read the Room therefore require explicit skill invocation for their full workflow/policy instructions; their existing hook configuration does not establish automatic instruction delivery. Do not replace startup instructions with a later tool hook and claim equivalent timing.

Disable, enable, update, and uninstall were checked for all six catalog packages. Use `grok plugin disable NAME` or `grok plugin uninstall NAME` to disable/remove a package; uninstall removes its installed entry and plugin skills from discovery. Refer to `grok plugin --help` for the installed version.
