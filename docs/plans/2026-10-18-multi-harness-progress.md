# Execution record: multi-harness support

Plan: [Multi-harness support](2026-10-18-multi-harness-support.md).

Status: scoped implementation and acceptance complete. Copilot CLI compaction and Pi disk-backed resume passed after explicit user approval. VS Code Local and VS Code Copilot are excluded. Changes remain uncommitted and unreleased. Scope: Copilot CLI, Grok Build, OpenCode, and Pi; Cascade, additional Agent Doctor host parsers, and native specialist agents remain deferred.

## Decisions

- Execute inline in the managed isolated worktree. Keep changes uncommitted for review.
- Reuse the existing root contributor dependencies without reinstalling or changing them.
- Existing Copywriter relocation tests already exercise sibling resources and bundled generators; run them before considering new coverage.

- Ruling: new Papercuts client journals use fixed user directories: Copilot `.copilot`, Grok `.grok`, OpenCode `.config/opencode`, Pi `.pi/agent`, each containing `papercuts.jsonl`. This extends the approved per-client user-journal design without moving existing data or adding storage overrides. Risk: these are Papercuts-owned default journal locations, not a promise to honor every host-specific data-directory override.

## Evidence

- Baseline: root tests passed 36/36; marketplace validation passed on the source checkout.
- New-host package metadata requests received HTTP 403 from the npm registry; an escalated metadata query succeeded; pinned Copilot 1.0.98, Pi 1.3.0, and OpenCode 1.19.3 were installed under temporary storage with lifecycle scripts disabled. No normal user configuration or authentication was inspected.

## Tasks

- Task 1: complete — compatibility matrix and contributor links added. Existing Copywriter relocation/deck test passed; Agent Doctor 3/3 tests and syntax validation passed; both complete relocated packages resolved 63 local references in a path with spaces. No redundant unit tests added.
- Task 2: distribution checks passed — Copilot 1.0.98 and Grok 1.0.62 installed/listed the four core packages (10 skills). Native catalogs added; two catalog validation regressions observed RED then GREEN; all 26 validator tests passed. Both local marketplace routes install eli5. Grok names a local source after its directory, not the catalog name; installation docs must use the registered name shown by marketplace list. Authenticated workflow invocation and desktop checks remain unverified.
- Task 3: active — OpenCode 1.19.3 discovered all 10 core skills through intact skill paths; Pi 1.3.0 installed the local root package and its native SDK resource loader discovered the same 10 skills with no diagnostics. Resource-path regression observed RED then GREEN.
- Tasks 4–8: pending.

## Implementation and verification checkpoint

- Task 3: native distribution metadata and local routes implemented. OpenCode/Pi skill loading verified. Existing root `scripts/` detection already covers the new adapters, so no redundant CI selector change was needed.
- Task 4: fixed-client storage and shared native MCP discovery implemented. All six client lifecycle cases pass; nested directory ancestry remains checked. Pi native tool round trip, Grok doctor, and Claude connection verified. Copilot effective registration is visible; its actual model tool invocation awaits sign-in.
- Task 5: shared canonical context loaders, native Copilot startup envelopes/configuration, OpenCode system/compaction hooks, and Pi owned system sections implemented. Legacy output/error tests pass. Native Pi runner confirms preserved host instructions. Model-backed and desktop lifecycle gates remain open.
- Task 6: Agent Doctor explicitly declines unsupported current-client settings and identifies unsupported session formats. No speculative parser or native-agent dependency was added.
- Task 7: Cascade runtime deferred: no exact installed product/version was verified in the standard application locations; no support badge was added.
- Task 8: implementation review complete; the reviewer found one Important coverage gap and no confirmed production regression. A regression reached by the repository test entrypoint now exercises both Papercuts adapters, relocated Pi MCP registration, host-policy preservation, and canonical policy reload. Authenticated and desktop acceptance checks remain open.

## Additional decisions

- Ruling: shared `.mcp.json` relies on actual plugin-root identity markers for Grok/Copilot/Claude; explicit client flags/environment retain precedence and the standalone default remains Codex. This avoids a shadowed Grok fallback manifest and duplicated service implementations. Risk: only the documented/tested host markers are recognized; other hosts require explicit selection.
- Ruling: native Copilot hooks use `.plugin/plugin.json` only for the two schema-free policy packages. Release enumeration now includes this version surface. Root-schema exceptions and existing native manifests remain in place.
- Ruling: new adapters live under existing root `scripts/` directories, so current scripted-plugin selection already reaches them. Static syntax checks now include `.mjs`.
- Ruling: no authenticated compatibility claim is made from static tests, listings, or successful transports. This preserves the plan's evidence gates rather than replacing them with an easier check.

## Access and export gates

- Actual Copilot and Grok model invocation failed because the isolated homes are not signed in. A user question about isolated test authentication is pending.
- Automatic approval review rejected a proposed OpenCode free-provider workflow because it would export local skill/prompt content without specific approval. No model request was sent; no alternate route was used. A separate approval question is pending.
- Pi model invocation also lacks provider authentication. Local native runner and MCP testing required none.
- VS Code 1.142.0 is installed, but separate Local/Copilot desktop workflow checks are still pending.


## Final local verification

- Root: 40/40 tests pass; marketplace validation and `git diff --check` pass.
- Agent Doctor: 3/3 tests and validation pass. Copywriter: 4/4 tests and validation pass. Read the Room: 13/13 tests and validation pass.
- Papercuts: the initial full 34-test suite and validation passed. After adding adapter coverage, the focused 9-test hook/adapter file passes. Two later full-suite runs failed only in the existing stale-lock contention test (34/35 passed on the latest run). The same unsafe-owner-file failure reproduced against an untouched HEAD package on the second focused attempt. This pre-existing intermittent failure remains unresolved; the full suite is not reported as consistently green.
- No external model request was sent. The temporary OpenCode server was stopped after local transport checks.
- Changes remain uncommitted in the managed worktree. No release, catalog publication, or compatibility badge promotion occurred.


## Distribution lifecycle completion

- A fresh isolated local marketplace copy with spaces in its path was tested with Copilot 1.0.98 and Grok 1.0.62. Both registered their native catalog, installed all six entries, and exposed 12 plugin skills. Each package passed disable, enable, update, and uninstall commands.
- Copilot's live route reports no work on update. Uninstall disables entries and retains checkout files; final skill discovery contains no plugin skills. Grok's final inventory contains no installed plugins or plugin skills. The installation guides now describe this distinction.
- Each host produced 40 successful command receipts, plus a final discovery check, in temporary evidence storage. No authentication or model request was needed.


## Approved native model checks and corrections

The user approved external model tests and reuse of existing Codex authentication, completed Grok device sign-in, approved trust for the synthetic workspace in the isolated VS Code profile, and completed desktop sign-in. Earlier access-gate notes above describe the previous checkpoint, not current missing permissions.

| Host/model | Observed behavior |
| --- | --- |
| Copilot CLI 1.0.98 / automatic MAI-Code-1.1-Flash route | Loads relocated eli5, recognizes automatic writing policy, and resumes for a tagged native Papercuts inspect/search/lodge/list round trip in `.copilot/papercuts.jsonl`. Existing GitHub CLI auth supplied the native token environment in memory; no credential cache was copied. |
| Grok 1.0.62 / grok-4.7 | Loads eli5 and explicitly invokes the policy skills. The first native MCP run incorrectly selected the standalone Codex journal. After the fix below, a fresh tagged complaint round trip uses `.grok/papercuts.jsonl`; the earlier Codex journal remains byte-for-byte unchanged. |
| OpenCode 1.19.3 / opencode/big-pickle | Loads eli5 through the native skill tool, recognizes automatic policy on first/second prompts, and completes an inspect/lodge/list round trip. Three tag-array calls fail because the model sends quoted JSON strings; untagged lodging succeeds. Native summarize returns 200 with a saved completed summary; authoritative session messages show a completed response after compaction retaining the policy and correct journal path. |
| Pi 1.3.0 / openai-codex/gpt-6.1-sol | Actual outbound request callbacks verify both canonical policies before model requests. Eli5, a tagged native MCP round trip, second prompt, native compaction, and post-compaction response pass. OAuth uses the existing valid access token in Pi's native in-memory store, without a refresh token, persisted credentials, or changes to Codex authentication. The isolated Pi auth file remains empty. |

Two integration defects were found and corrected:

1. Grok substitutes plugin-root tokens but does not export those identity markers to its MCP child. Papercuts now names `.grok-plugin/mcp.json` from its schema-free root and explicitly sets `PAPERCUTS_CLIENT=grok`. Copilot's `.plugin/plugin.json` explicitly names `.mcp.json`, which sets its own client. Guessed marker inference was removed. Offline tests now launch the selected native configuration rather than supplying the client independently. A real corrected Grok round trip and Copilot storage probe verify the selection. Claude still connects with these final metadata changes.
2. VS Code Local exports `PLUGIN_ROOT` for the selected plugin format. Native hook logs showed that commands requiring only `CLAUDE_PLUGIN_ROOT` failed before model delivery. Shared hook commands now resolve either environment through Node, avoiding shell-specific variable fallback syntax. Existing relocated tests reproduce the Local failure and pass after the correction, including Read the Room's prompt reminder. Payload construction and legacy envelopes remain unchanged.

The root validator now accepts contained JSON MCP paths only for schema-free native roots. A focused fixture proves portable-schema rejection, missing resources, path escape, and symlink escape. Root tests pass 41/41 and marketplace validation passes. Read the Room passes 13/13 and validation. Papercuts passes its latest full 34/34 suite and validation; its earlier intermittent stale-lock failure still reproduces on untouched HEAD and is not claimed fixed.

VS Code 1.142.0 with bundled Copilot Chat 0.70.0 displays six local plugins and 12 plugin skills with intact source paths. Its first Local model response loads eli5, but that response cannot prove automatic policy: native logs show startup/reminder failures, and the model separately read the writing skill. Fresh desktop verification after the command fix remains open. The UI connector repeatedly reports stale elements and missing native windows despite a live isolated process, including after reset. A documented `code chat` submission returned success with option warnings but produced no saved corrected request; it is not counted as verification. The Copilot desktop session type remains separately unverified.

The temporary OpenCode loopback server was stopped. Changes remain uncommitted; no release or support badges were published.


## Remaining test approval review

Automatic approval review rejected the additional Pi disk-resume request and the native Copilot compaction session as insufficiently specific about external payloads/destinations and, for Copilot, allowed tool execution. Neither rejected action ran. This is separate from the earlier approved and completed model checks above. The remaining test sheet now names the exact synthetic prompts, OpenAI/GitHub destinations, credential handling, and isolated Papercuts write scope; a grouped approval question is pending. Papercuts execution is not needed for the CLI compaction check and is excluded from that proposal.

Latest deterministic checks after both fixes: root 41/41, Read the Room 13/13, Papercuts 34/34, all applicable validation entrypoints, and whitespace checks pass. Agent Doctor and Copywriter's earlier required entrypoint checks still apply because their executable code has not changed since those checks. No complete-goal claim is made: desktop behavior after the hook fix and the remaining lifecycle cases are open.


A final isolated Claude native-selection probe retained the complete final metadata and wrapped only the bundled entrypoint to record the non-secret client selector. Claude 2.1.268 connects and the actual MCP child receives `PAPERCUTS_CLIENT=claude`; the new root/Copilot MCP files do not redirect Claude into another client's journal. No model call or user journal write was needed.


## Final audit follow-up

- The validator still required a Codex/Claude native manifest before allowing a schema-free root, even for a Copilot-only catalog package with its own valid native manifest. A focused fixture reproduced that rejection. Including `.plugin/plugin.json` in the existing native-manifest check fixes the contributor contract without adding another client's files. Root tests now pass 42/42, marketplace validation passes, and whitespace checks pass.
- The desktop UI connection recovered on revalidation. Its actual picker confirms that Local uses the proprietary extension-host harness and Copilot uses the SDK Agent Host. The current Local request is terminal with its eli5 answer; no duplicate request was sent. No harness switch or additional model request was made while the grouped approval remained pending. UI targeting has been intermittent rather than permanently unavailable.


## Same-name source audit

Copilot CLI 1.0.98's native `skill list --json` was exercised with an installed eli5 package, an isolated personal same-name fixture, and a separate synthetic project's same-name fixture. The selected source was project over personal over plugin. Removing the project fixture restored the personal source; removing the personal fixture restored the original complete plugin path. Both temporary fixture files were removed. This closes the CLI portion of the plan's explicit shadowing check without model inference. Desktop source/lifecycle acceptance remains open; no additional approval was inferred.


Blocked audit: the remaining external-model approval has stayed pending across three consecutive goal turns. The final read-only/local audit completed the CLI shadowing check; desktop revalidation again returned `cgWindowNotFound`. No rejected model request was retried, no approval was inferred, and no further required local implementation work was identified. Resume the remaining native test sheet after explicit approval and a usable desktop window connection.


## Scope revision: desktop harnesses excluded

The user removed VS Code Local and VS Code Copilot from this iteration and retained Copilot CLI. The plan, compatibility matrix, and Copilot installation guide now reflect that boundary. Earlier desktop observations and the resulting shared-hook regression fix are retained as historical evidence; no desktop certification or further desktop model tests are required. The pending test proposal is narrowed to Copilot CLI compaction and Pi disk-backed resume. Neither previously rejected CLI test has run, and this scope change does not authorize those external model requests.


## Final scoped acceptance

The user approved the remaining CLI tests after excluding both desktop harnesses. Pi used native SessionManager disk creation/open in separate processes; each request included both canonical policies, and the resumed response recovered `PI_NATIVE_RESUME_7281` and `Make It Make Sense`. Existing Codex OAuth remained in memory only, without refresh; the isolated Pi auth store is still empty. Receipts: `pi-disk-create.txt` and `pi-disk-resume.txt` under the existing temporary evidence root.

Copilot CLI resumed its synthetic session and ran native `/compact`. Its saved event stream records `session.compaction_complete` with success, 21 messages removed, and a saved checkpoint. The post-compaction response reported `Make It Make Sense` and the correct isolated `.copilot/papercuts.jsonl` path. Papercuts and shell execution were denied and built-in MCPs disabled for these checks. Receipts: `copilot-approved-compaction.json`, `copilot-approved-post-compaction.json`, and the native session event/checkpoint files. No desktop model request was made.

Final required checks passed: root 42/42 plus marketplace validation; Read the Room 13/13, Papercuts 34/34, Agent Doctor 3/3, Copywriter 4/4, and each plugin's validation entrypoint. Logs use the `checks/final-scoped-` prefix under the temporary evidence root. The previously reproduced baseline Papercuts stale-lock race remains a known intermittent test limitation; this final run passed. Whitespace validation also passes.

The implementation goal is complete within the revised scope. Additional provider/workflow combinations, OpenCode model tag serialization, fresh authenticated Codex/Claude policy behavior, deferred Agent Doctor/native-agent features, and Cascade remain explicitly unverified or deferred. No release, commit, push, support badge, dependency addition, or normal-user configuration change was performed.
