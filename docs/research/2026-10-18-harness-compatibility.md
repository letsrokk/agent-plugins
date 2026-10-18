# Coding harness compatibility investigation

Expand this repository's reach by keeping the shared `plugins/` payload and adding only the distribution metadata and runtime adapters each supported harness needs. Prioritize working skills before promising automatic hooks or native specialist agents.

Status: research and proposed architecture, checked **2026-10-18**. Local baseline: `9348d1fa6f8753d6fd79e57748ce110ac0e61db8`. This investigation changed no plugin, catalog, user configuration, or installed client. The [proposed implementation plan](../plans/2026-10-18-multi-harness-support.md) turns the findings into independently shippable work.

**Iteration scope:** Copilot CLI, Grok Build, OpenCode, and Pi; Windsurf / Devin Desktop remains a later skills-only investigation. Preserve existing Codex and Claude support. VS Code Local, VS Code Copilot, Qwen Code, Gemini CLI, Amp, Cline, and Cursor are excluded from this iteration. Their findings below remain background research and do not authorize implementation, certification, catalogs, or installation documentation.

## Evidence and support vocabulary

Documentation support means the provider documents a capability. Source support means the inspected implementation contains it. Neither proves this repository's package works in an installed release. Record a supported host version only after an isolated installation and behavioral check.

Use separate support records for:

- **Skills:** discovery, invocation, reference loading, and the requested workflow.
- **Tools:** MCP startup, tool discovery, calls, and application storage behavior.
- **Automatic instructions:** startup, subsequent prompts, resume, and compaction as applicable.
- **Native agents:** host-discovered specialist agents and delegation.
- **Distribution:** installation, updates, removal, and package integrity.

The [Agent Plugins v1 specification](https://agent-plugins.org/specification) standardizes root metadata, `skills/`, and `mcp.json`; hooks and agents are client extensions. [Agent Skills](https://agentskills.io/specification) standardizes a skill's instructions and resources. Support for either format, `AGENTS.md`, a model provider, or MCP alone does not establish complete plugin compatibility.

## Current repository constraints

There are seven plugins and 15 skills. All seven appear in the Codex catalog; only agent-doctor, copywriter, papercuts, and read-the-room appear in the Claude catalog. Root manifests for five plugins declare Agent Plugins v1. Papercuts and Read the Room deliberately omit the schema to retain native Codex loading.

| Plugin | Reusable core | Expansion constraint |
| --- | --- | --- |
| eli5 | One skill with standalone HTML fallback | Verify file delivery and browser availability separately |
| code-simplifier | One skill and local execution fallback | Specialist definition is Codex TOML, not a portable agent |
| pr-review-toolkit | One skill and local review fallback | Six specialist definitions are Codex TOML |
| copywriter | Seven skills and bundled Node generators | Preserve sibling skills, root scripts, and bundled assets |
| read-the-room | One skill with channel references | Automatic policy injection uses native hook contracts |
| papercuts | One skill, bundled stdio MCP, and service | Native-only MCP declarations; client/storage allowlist is Codex/Claude |
| agent-doctor | Three inspection skills | Host settings and usage analysis currently cover Codex/Claude |

Relevant local contracts:

- [Contributor workflow](../plugin-development.md): one shared payload, manually maintained catalogs, Node.js 24+, bundled runtime dependencies, and synchronized release manifests.
- [Marketplace validator](../../scripts/validate_marketplaces.js): only Codex/Claude catalogs and native-manifest exceptions are recognized; root component fields are rejected; custom-agent checks understand TOML.
- [Release automation](../../scripts/version_plugins.js): version surfaces are explicitly `plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`.
- [CI selection](../../scripts/plugin_ci.js): scripted detection covers root `src/`, root `scripts/`, and skill scripts, but not arbitrary host-extension directories.
- [Papercuts paths](../../plugins/papercuts/src/paths.js): client selection and user journals explicitly allow only `codex` and `claude`.
- [Copywriter landing page](../../plugins/copywriter/skills/landing-page/SKILL.md) and [deck skill](../../plugins/copywriter/skills/pitch-deck/SKILL.md): `../../scripts` dependencies. Its skills also reference sibling `write/` resources. Agent Doctor references shared prompting files outside individual skill directories.

Consequently, an installer that copies only a selected `SKILL.md` directory is unsuitable for all packages. Clone or install the complete plugin, register its existing skill paths, and prove relocation works. Do not duplicate support files into every skill to accommodate a destructive installation topology.

## Harness comparison

These are researched adoption routes, not newly certified support claims. Each row links the provider's contract; the detailed sections explain material limits. Excluded targets are retained for reference only.

| Target | Package route | Existing skills | Runtime work | Recommendation |
| --- | --- | --- | --- | --- |
| [Copilot CLI](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) | Agent Plugins or legacy plugin; native marketplace | Portable roots are candidates | MCP declaration and hook output adapter | First cohort |
| [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins) | Agent Plugins and native formats | Portable roots are candidates | Test Local and Copilot harnesses separately | Separate certification rows |
| [Cursor](https://prod.cursor.com/docs/reference/plugins) | Agent Plugins or Cursor native manifest/catalog | Portable roots are candidates | Native hooks/agents and variable differences | Excluded this iteration |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/extension/agent-plugins/) | Native Agent Plugins support | Five portable roots are candidates | Native extension needed for broader components | Excluded this iteration |
| [Grok Build](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/09-plugins.md) | Grok/Claude-style plugin and marketplace | Layout matches; loader differs from v1 | Root precedence, MCP registration, startup semantics | First cohort, explicit limits |
| [OpenCode](https://opencode.ai/docs/plugins/) | Skill paths plus JS/TS plugins | Register intact package paths | Native context adapter and MCP configuration | Second cohort |
| [Pi](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/docs/packages.md) | `package.json` resources and extensions | Package-relative paths work | Native context/MCP extension | Second cohort |
| [Gemini CLI](https://geminicli.com/docs/extensions/reference/) | `gemini-extension.json` | Existing extension `skills/` layout fits | Native MCP metadata and hook event mapping | Excluded this iteration |
| [Amp](https://ampcode.com/docs/customize/plugins) | JS/TS directory plugin or skill paths | Register intact paths | Skill registration and lifecycle adapter | Excluded this iteration |
| [Windsurf / Devin Desktop](https://docs.devin.ai/desktop/cascade/skills) | Skills plus separate native customization | Documented skill discovery | No common package route established | Skills-only investigation |
| [Cline](https://docs.cline.bot/customization/plugins) | Skills; separate executable plugin SDK | Documented skill discovery | SDK-specific runtime port | Excluded this iteration |

### Copilot CLI and VS Code

Copilot CLI recognizes portable root manifests and legacy formats. Its legacy root manifest wins over `.claude-plugin/plugin.json`; MCP from a shadowed Claude manifest is therefore not inherited. The existing Claude marketplace is discoverable but exposes only four plugins. A dedicated, manually maintained `.github/plugin/marketplace.json` can select the eligible shared packages without expanding the Claude catalog. [CLI discovery and catalog reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

The CLI's documented startup result is top-level `additionalContext`; existing scripts emit the nested Claude envelope. PascalCase event aliases do not establish output compatibility, and nested matcher-group acceptance remains unverified. Supply a native configuration/output adapter and test context delivery. [Copilot hook contract](https://docs.github.com/en/copilot/reference/hooks-reference)

VS Code's Local harness accepts nested Claude configurations but ignores matchers. Its startup output accepts the existing nested envelope. Copilot-backed sessions use the Copilot contract instead. Treat CLI, VS Code Local, and VS Code Copilot as distinct test targets, including trust and enablement state. [VS Code plugin hooks](https://code.visualstudio.com/docs/agent-customization/agent-plugins), [Local hook contract](https://code.visualstudio.com/docs/agents/reference/hooks-reference)

Copilot agents use Markdown and native frontmatter, not the nested Codex TOML files here. Local skill execution is the initial supported route. [Custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

### Grok Build

This investigation means xAI's official coding harness, not the Grok model running in another application. Inspected source commit `2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8`, dated September 29, 2026, identifies pager version 1.0.45. It is source evidence, not certification of a downloaded binary.

The selected manifest order is root `plugin.json`, `.grok-plugin/plugin.json`, then `.claude-plugin/plugin.json`. Unknown fields are ignored; this is not schema-selected Agent Plugins v1 loading. Defaults include `skills/`, `hooks/hooks.json`, and `.mcp.json`. A new Grok manifest alone cannot override the existing root, so Papercuts still needs MCP in a configuration the selected loading route reads. [Pinned manifest implementation](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-agent/src/plugins/manifest.rs)

Grok accepts the nested hook configuration and plugin-root aliases. However, its documented passive `SessionStart` hook ignores stdout, and prompt-hook context does not provide the same injection behavior. Moving policy to a tool hook changes when the model receives it. Ship explicit skill invocation first unless a verified native mechanism supplies policy before the first response. [Hook adapter source](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-agent/src/plugins/hooks_adapter.rs), [Hook semantics](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md)

A dedicated `.grok-plugin/marketplace.json` is a native discovery option using relative sources. Validate with the released binary before advertising install syntax or hook parity. [Pinned marketplace parser](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-plugin-marketplace/src/index.rs), [Plugin validation and trust](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/09-plugins.md)

### Cursor and Qwen Code (excluded this iteration)

Cursor supports portable skills/MCP and a richer native `.cursor-plugin/plugin.json`. Its repository import needs `.cursor-plugin/marketplace.json`; keep its entries hand-authored over the shared tree. Native agents use Markdown. MCP variable support differs: use documented Cursor/Claude root variables rather than assuming standard root/data variables expand. A symlink from Cursor's local plugin directory to an external checkout is not a supported installation shortcut. [Cursor reference](https://prod.cursor.com/docs/reference/plugins), [Repository import and skill discovery](https://prod.cursor.com/docs/skills), [Local plugin development](https://prod.cursor.com/docs/plugins)

Cursor's Claude hook compatibility is promising, but exact startup and prompt-context delivery still needs behavioral verification. [Third-party hooks](https://cursor.com/docs/reference/third-party-hooks)

Qwen's September 16 documentation states direct v1 loading without conversion or a new native extension manifest. Skills and stdio/Streamable HTTP MCP are supported; v1 hooks, agents, workflows, and legacy SSE are not. This makes the five portable roots good initial candidates, subject to actual discovery and invocation. [Qwen portable contract](https://qwenlm.github.io/qwen-code-docs/en/users/extension/agent-plugins/)

Qwen's extension sources also accept Claude marketplaces. Investigate that route before creating another catalog. Clone plus `qwen extensions link ./plugins/eli5` is a documented local topology; monorepo remote selection remains a smoke-test requirement. Native `qwen-extension.json` can be considered later where portable loading is insufficient. [Qwen extension distribution](https://qwenlm.github.io/qwen-code-docs/en/users/extension/introduction/)

### OpenCode

Inspected release: v1.19.3, released October 16, 2026. Standard skill discovery and executable JS/TS plugins are separate features. Register absolute `skills.paths` entries pointing at complete plugin checkouts; these preserve package-root and sibling references. The remote `skills.urls` index downloads skills independently, so it is not automatically a package-preserving Git installer. [Skills documentation](https://opencode.ai/docs/skills/), [Pinned discovery](https://github.com/anomalyco/opencode/blob/v1.19.3/packages/opencode/src/skill/index.ts), [Remote download topology](https://github.com/anomalyco/opencode/blob/v1.19.3/packages/opencode/src/skill/discovery.ts)

A native JS module can append owned instructions through `experimental.chat.system.transform`; compaction has a separate experimental hook. A session-created notification alone does not inject model context. Pin the experimental API version and verify compaction behavior. Use native local MCP with the existing `dist/mcp_server.js` rather than duplicating tools in JavaScript. [Plugin interface](https://github.com/anomalyco/opencode/blob/v1.19.3/packages/plugin/src/index.ts), [Native MCP](https://opencode.ai/docs/mcp-servers/)

OpenCode native agents use Markdown or configuration entries. Keep the existing local fallback before adding another agent representation. [Agents](https://opencode.ai/docs/agents/)

### Pi

Pi v1.3.0, released October 15, 2026, has native MCP; older descriptions requiring a third-party bridge are stale for this release. Core still does not provide the optional example's subagent orchestration. [Release](https://github.com/earendil-works/pi/releases/tag/v1.3.0), [Core scope](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/README.md)

Pi packages declare package-relative resources in `package.json` under `pi`. A root entry selecting `./plugins/<name>/skills` can retain the complete repository layout; local per-plugin installation is another candidate. Do not invent a Git subdirectory selector. Git installs discover the cloned root and run production dependency installation there; local packages do not copy or install dependencies. Repository `private: true` blocks npm publication, not Git/local package use. [Package contract](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/docs/packages.md), [Pinned installer](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/src/core/package-manager.ts)

The native extension can register Papercuts with `pi.registerMcpServer`, keeping the committed bundle and avoiding a third-party bridge. Decide direct versus codemode exposure deliberately and verify actual tool availability. Native file configuration can override a duplicate registration. [Pi MCP](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/docs/mcp.md)

For automatic policy, use a small extension and `before_agent_start` context rather than printing Claude JSON. `appendEntry` alone stores state without giving it to the model. Keep the existing local specialist fallback; do not depend on an optional subagent example as though it were core. [Extension interfaces](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/src/core/extensions/types.ts), [Optional subagent example](https://github.com/earendil-works/pi/tree/v1.3.0/packages/coding-agent/examples/extensions/subagent)

### Gemini CLI (excluded this iteration)

Per-plugin `gemini-extension.json` can reuse existing `skills/` and package resources. MCP uses extension metadata and `${extensionPath}`. Clone plus local per-plugin install/link is the verified documentation route; remote monorepo subdirectory installation is not established here. [Extension contract](https://geminicli.com/docs/extensions/reference/)

Gemini startup context uses a nested envelope, but prompt processing uses `BeforeAgent`, not Claude's `UserPromptSubmit`. Adapt the event registration, root variable, and output event name together. Native subagents are preview; omit them from the initial support promise. [Hooks](https://geminicli.com/docs/hooks/reference/), [Skills](https://geminicli.com/docs/cli/skills/)

### Amp (excluded this iteration)

Amp's current plugins are executable JS/TS modules. A directory plugin must explicitly register its skills; `skills/` is not automatically scanned as plugin content. It offers lifecycle events, including an `agent.start` result that can append turn instructions. This is a native adapter opportunity, not ingestion of this repository's manifests. [Amp plugins](https://ampcode.com/docs/customize/plugins)

Alternatively, `amp.skills.path` can expose intact local package resources. Prefer this over assuming a remote skill copy retains Copywriter's parent files. Amp also supports skill-scoped MCP with its own configuration shape; its skill `mcp.json` is not the same contract as portable plugin-root `mcp.json`. [Amp skills](https://ampcode.com/docs/customize/skills), [Amp MCP](https://ampcode.com/docs/customize/mcp)

### Windsurf / Devin Desktop

The official Windsurf skill documentation currently redirects to Devin Desktop. Current Cascade supports standard skills and legacy Windsurf locations; this does not prove the same features exist in an older installed Windsurf release. No common marketplace loader was established. [Current Cascade skills](https://docs.devin.ai/desktop/cascade/skills)

### Cline (excluded this iteration)

Cline skills are viable candidates. Its separate executable plugin API uses `AgentPlugin` modules and `package.json` metadata, and currently targets SDK, CLI, and Kanban, not VS Code/JetBrains. Do not advertise one undifferentiated Cline plugin badge. [Cline skills](https://docs.cline.bot/customization/skills), [Cline executable plugins](https://docs.cline.bot/customization/plugins)

## Proposed architecture and tradeoffs

Three approaches are possible:

1. **Skills-only distribution:** smallest initial work, but drops automatic policies, MCP setup, and native agents. It is suitable only with component-specific limitations and package-preserving installation.
2. **Shared payload with native metadata and small adapters — recommended:** retain current package ownership, add deliberate catalogs/manifests only where required, and reuse the existing bundled service/generators. Maintenance grows with the actual supported runtime surface.
3. **Per-harness forks or a universal manifest compiler:** creates duplicated payloads or a second platform to maintain. It conflicts with the repository's manual-catalog rule and is unnecessary for seven plugins.

Keep root-schema exceptions until current Codex behavior is rechecked. A portable MCP file alone does not fix a loader that selects native mode; a new native fallback manifest does not fix a loader that selects the existing root. Test the selected configuration, not just whether a file exists.

Use core workflows as the first certification slice: eli5, code-simplifier, pr-review-toolkit, and Copywriter. The last three still need meaningful behavior checks, including Copywriter's complete package resources. Agent Doctor receives a scoped capability claim, not a claim to audit an unsupported current host. Add Papercuts and automatic writing policy separately.

Papercuts expansion must explicitly add supported client identifiers and per-client user storage while preserving existing journals and error handling. Do not infer the client from the selected model or silently route new hosts into Codex/Claude storage. No project journals, arbitrary journal overrides, or migration are proposed.

Do not extract a generic hook protocol, client registry, or agent-definition compiler upfront. A shared text-loading helper is justified only when the first real adapter would otherwise duplicate the same policy construction. Keep each host's event names, envelope, and lifecycle decisions visible in its adapter.

## Certification and release requirements

For each promoted host/plugin/component pair, retain the exact host version, OS, source revision, package version, installation route, enablement/trust state, and sanitized observed result. Use isolated homes and a relocated checkout with spaces in its path. Run offline after installation where the plugin claims bundled execution.

| Capability | Evidence required before promotion |
| --- | --- |
| Skills | List/discover the intended skill, invoke it, and read referenced resources from the relocated package |
| Code workflows | Respect explicit edit/review scope; use local fallback without unavailable agent tools |
| Copywriter | Generate an actual requested artifact using the committed bundle; state unavailable visual checks |
| Papercuts | Initialize MCP, list tools, lodge/list a synthetic complaint in an isolated user home, and verify selected client storage |
| Automatic policy | Observe policy before the first response without skill invocation; check later turns and supported resume/compaction behavior |
| Distribution | Install, disable/remove, update, and verify no unintended catalog or root-manifest shadowing |
| Native agents | Demonstrate discovered role and actual delegation, only if advertised |

Static fixtures should cover real schema/configuration contracts and selected-manifest regressions. They do not replace host checks. Keep paid/authenticated behavioral smoke tests separate from deterministic pull-request CI, and never mark unavailable checks as passed.

Update release surface enumeration whenever a version-bearing native manifest is introduced. Add executable adapters to scripted-plugin selection and static validation. Preserve the installed Node-only requirement: bundling is a contributor operation, not a hook or server startup action.

## Verification performed and gaps

The existing root checks ran on Node.js v26.12.0: `npm test` passed all 36 tests and `npm run validate` printed `Marketplace validation passed.` These check current repository contracts, not new-host compatibility.

Only `codex` was available among the checked CLI executable names. No new harness was installed, authenticated, invoked, or configured. No plugin hooks, MCP servers, generators, or plugin-specific suites were executed. Desktop application inventories and account entitlements were not inspected. Web evidence is current documentation or the pinned source/release identified above; source snapshots are not a substitute for released-binary testing.
