# Harness compatibility

This matrix separates package installation, workflow behavior, MCP tools, automatic policy, and native agents. The added harness routes are experimental. A verified listing or transport connection is not a blanket compatibility claim.

## Scope and package integrity

This iteration targets Copilot CLI, Grok Build, OpenCode, and Pi. VS Code Local and VS Code Copilot are excluded from this iteration; earlier desktop observations below are historical evidence, not acceptance gates. Windsurf / Devin Desktop is a later skills-only investigation. Cursor, Qwen Code, Gemini CLI, Amp, and Cline are excluded. Existing Codex and Claude distribution stays in place.

Keep the complete `plugins/<name>/` directory. Copywriter requires sibling skills and root generators; Agent Doctor requires shared prompting references. Copying one skill directory can lose those resources. code-simplifier and pr-review-toolkit apply specialist instructions locally when native delegation is unavailable.

Checked 2026-10-18 on macOS with Node.js 26.12.0, against baseline `9348d1fa6f8753d6fd79e57748ce110ac0e61db8` plus the uncommitted implementation. `Documented` and `source-checked` describe provider evidence; `verified` identifies an observed local operation. The PR was subsequently rebased onto the Read the Room 0.6.3 metadata-only release, and its new Copilot manifest was synchronized. New release versions will follow the existing synchronized version policy.

| Plugin | Source package version |
| --- | --- |
| eli5 | 0.2.0 |
| code-simplifier | 0.1.5 |
| pr-review-toolkit | 0.1.3 |
| copywriter | 0.3.1 |
| read-the-room | 0.6.3 |
| papercuts | 0.4.6 |
| agent-doctor | 0.3.1 |

## Native evidence

| Harness/surface | Version | Verified operation | Remaining limits |
| --- | --- | --- | --- |
| Codex | 0.163.0 | Local Codex marketplace registration; Papercuts and Read the Room installed and enabled | Fresh authenticated policy/model behavior not checked; hook trust remains a separate host step |
| Claude Code | 2.1.268 | Packaged Papercuts MCP still connects after explicit Grok/Copilot configuration was added; an actual child-process probe confirms `PAPERCUTS_CLIENT=claude` | Model behavior not checked; shared hook commands pass relocated-package tests with the Claude root environment |
| Copilot CLI | 1.0.98 | Six local-marketplace packages expose 12 skills; distribution lifecycle checked; signed-in eli5 invocation and automatic writing policy observed; resumed native MCP lodge/list round trip uses the Copilot journal with a real tag array; native manual compaction succeeds and the following response retains the policy title and journal path | Additional workflow/model combinations remain unverified |
| VS Code Local | 1.142.0; bundled Copilot Chat 0.70.0 | Isolated signed-in/trusted profile displays six plugins and 12 plugin skills at their intact source paths; eli5 response and actual resource reads observed | Native logs exposed failed shared hooks because only `PLUGIN_ROOT` was exported. Commands were fixed and regression-tested; a fresh native request after the fix remains unverified. Excluded from this iteration; no further desktop verification is planned |
| VS Code Copilot | 1.142.0; bundled Copilot Chat 0.70.0 | Desktop sign-in completed by the user; the native picker separately identifies the Copilot SDK Agent Host | Excluded from this iteration; model behavior and lifecycle remain unverified, and CLI results do not certify it |
| Grok Build | 1.0.62 (`1474f9cbdd91`), grok-4.7 | Six marketplace packages expose 12 skills; eli5 and explicit policy invocation observed; corrected native MCP lodge/list round trip uses the Grok journal and a tag array, leaving the earlier Codex test journal unchanged | Startup stdout does not inject policy. The selected root must name its explicit Grok MCP configuration; fallback metadata and transport health alone were insufficient |
| OpenCode | 1.19.3, opencode/big-pickle | Intact paths expose 10 core skills; eli5 loads through the native skill tool; automatic writing policy observed on first/second prompts and after native compaction; native MCP completes inspect/lodge/list in its own journal | The model sent tag arrays as quoted strings across three failed attempts; lodging succeeded without tags. Tagged model calls and other provider/workflow combinations remain unverified |
| Pi | 1.3.0, openai-codex/gpt-6.1-sol | Local package/resource loading; actual outbound requests contain both canonical policies; eli5 invocation, tagged native MCP round trip, second prompt, native compaction, post-compaction response, and disk-backed resume in a separate process pass | The complete workflow inventory remains unverified. Codex OAuth was supplied only to an in-memory native store, without saving or refreshing credentials |
| Windsurf / Devin Desktop | No exact runtime verified | Current Cascade documentation only | No standard application bundle found in the checked `/Applications` locations; deferred with no new support claim |

Core packages are eli5, code-simplifier, pr-review-toolkit, and copywriter. Copilot and Grok catalogs additionally expose Read the Room and Papercuts with the limitations above. The Pi root package selects those six packages and the two native policy extensions. Agent Doctor is not promoted to new-host settings or usage support; its descriptions now state that boundary explicitly.

## Observed checks

All installs, configuration changes, synthetic complaints, and native server checks used isolated temporary homes. Normal user settings were not modified. After explicit user approval, tests reused existing Codex/GitHub credentials only in memory; the user signed in to the isolated Grok and VS Code homes. Host binaries were pinned in temporary storage, with install scripts disabled; platform binaries were selected directly where their npm launcher needed a postinstall step.

| Check | Observed result |
| --- | --- |
| Copywriter existing package test | Three relocated release layouts generate actual editable decks and SVG previews without npm on PATH |
| Complete Copywriter and Agent Doctor relocation | All 63 local skill/reference links resolve inside intact packages relocated into a path containing spaces |
| `copilot plugin install` and `copilot skill list` | Core packages expose 10 skills; direct installs warn of deprecation |
| Copilot same-name skill precedence, `skill list --json` | A project eli5 fixture overrides the personal fixture, which overrides the plugin; removing each fixture restores the next source and finally the intact plugin path. No model call was needed. |
| `copilot plugin marketplace add` and marketplace install | Local catalog selected as `rokk-club-copilot-plugins`; all six packages load live from intact packages in a path with spaces |
| `grok plugin install`, `grok inspect --json`, and native marketplace install | All six packages and 12 skills discovered; local source registration uses its directory name, not the manifest name |
| Native CLI distribution lifecycle, all six packages | Disable/enable/update/uninstall commands succeed. Copilot live updates require no copy and uninstall disables entries without removing checkout files; disabled skills disappear. Grok uninstall removes installed entries and plugin skills. |
| `grok plugin validate` with conflicting fallback metadata | Root `papercuts` identity/version wins |
| `grok mcp doctor` | Packaged Papercuts server starts, handshakes, and exposes nine tools |
| `claude --plugin-dir ... mcp list` | Packaged Papercuts server connects |
| `codex plugin marketplace add`, `plugin add`, and `plugin list` | Existing native catalog and both policy plugins install/enable successfully |
| `opencode debug skill` | All 10 core skills load through explicit paths |
| Native OpenCode localhost `GET /mcp` | Papercuts reports connected; server used a temporary password and loopback binding |
| Pi native `DefaultResourceLoader` | Core resources resolve without diagnostics |
| Pi native `ExtensionRunner.emitBeforeAgentStart` | Existing host system section is retained and both owned policy sections are prepared |
| Approved model sessions | Copilot and Grok invoke eli5 and complete tagged native MCP round trips; Pi additionally verifies outbound policy and real compaction. OpenCode invokes eli5, completes an untagged round trip, and retains policy after compaction; tag serialization failed for the selected model. |
| VS Code Local native hook log | Before the fix, all three shared commands failed to locate their scripts because only `PLUGIN_ROOT` was exported. The same environment now passes the relocated hook tests. |
| Pi native session after `bindExtensions` | Nine native Papercuts tools become active; lodge/list/inspect round trip uses the isolated `.pi/agent/papercuts.jsonl` journal |

The root tests, affected plugin suites, static validation, and document checks are tracked in the [execution record](plans/2026-10-18-multi-harness-progress.md). Their assertions do not replace an authenticated model run.

## Installation

Use an intact checkout containing these changes until a release publishes the new routes:

- [Copilot CLI](installation/copilot.md)
- [Grok Build](installation/grok.md)
- [OpenCode](installation/opencode.md)
- [Pi](installation/pi.md)

For new verification, retain exact client/plugin versions, OS, source revision, installation route, trust state, evidence date, command/result, and remaining limits. Authenticate test homes separately; never paste tokens into reports. Do not upgrade an unavailable or rejected check to verified.

## Remaining compatibility limits

- Additional workflow/provider combinations beyond the smoke cases above remain unverified.
- OpenCode model-driven tag arrays with the selected free provider. External-provider export approval was granted and those smoke runs completed. After specific user approval, the previously rejected Pi disk-resume and Copilot CLI compaction tests ran successfully. Desktop tests were excluded by the user.

Native specialist agent definitions and new Agent Doctor history parsers are deliberately deferred; local execution and explicit unsupported-host behavior remain the implemented contract. See the [investigation](research/2026-10-18-harness-compatibility.md) and [plan](plans/2026-10-18-multi-harness-support.md).
