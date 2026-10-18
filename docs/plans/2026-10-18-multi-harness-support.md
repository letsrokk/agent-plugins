# Multi-harness support implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` for approved implementation. Subagent-driven execution is an alternative only if selected later. Checkboxes track execution. See the linked execution record for native evidence and access gates.

**Goal:** Make selected existing plugins usable across more coding harnesses without duplicating the shared payload or overstating feature support.

**Architecture:** Keep `plugins/<name>/` as the package boundary. Add manually maintained native catalogs and distribution metadata where required, then small adapters for supported lifecycle and MCP contracts. Certify skills, tools, automatic instructions, native agents, and distribution independently.

**Tech stack:** Existing Node.js 24+ repository tooling and bundled plugin runtimes; native JSON metadata and minimal JavaScript/TypeScript only where a harness requires it. No universal installer or manifest compiler.

**Spec:** [Research, current constraints, proposed architecture, and primary sources](../research/2026-10-18-harness-compatibility.md).

**Status:** Scoped implementation and acceptance complete; changes remain uncommitted and unreleased. Local implementation and native loader/transport checks are recorded in the [execution record](2026-10-18-multi-harness-progress.md). Approved CLI model smoke tests, Copilot CLI compaction, and Pi disk-backed resume have completed; limitations are recorded in the execution record; experimental distribution is not blanket compatibility certification.

**Iteration scope:** Copilot CLI, Grok Build, OpenCode, and Pi; Windsurf / Devin Desktop remains a later skills-only investigation. Preserve existing Codex and Claude support. VS Code Local, VS Code Copilot, Qwen Code, Gemini CLI, Amp, Cline, and Cursor are excluded from this iteration, including catalogs, adapters, certification, and installation documentation.

## Global constraints

- One shared `plugins/` tree; do not generate catalogs or duplicate plugin payloads between client trees.
- Preserve the existing Codex and Claude catalogs, names, policies, and working behavior.
- Catalog sources must be exactly `./plugins/<plugin-name>`.
- Repository tooling and installed scripted workflows require Node.js 24 or later; runtime dependencies remain bundled.
- Every new scripted plugin surface must be reached by its existing no-argument `scripts/test.js` and `scripts/validate.js` entrypoints and CI selection.
- Existing root-schema omissions remain until released-host evidence justifies changing them.
- Preserve current user journals. No project/custom journals, arbitrary storage configuration, or automatic migration.
- New release manifests must participate in synchronized stable `MAJOR.MINOR.PATCH` versioning.
- Report component-level limitations. A skill listing is insufficient to claim automatic hooks, MCP functionality, host-settings inspection, or native agents.
- No installs into normal user homes, account changes, publication, commits, or pushes are part of this execution. Native test tools use isolated temporary homes.

## Review focus

1. Relocated packages and paths with spaces must preserve sibling references, root scripts, and bundled assets. Task 1 owns this check.
2. A valid fallback manifest must not conceal selected-root precedence or silently drop MCP configuration. Tasks 2 and 4 own this check.
3. Startup policy must reach the model before its first response and survive only the lifecycle transitions explicitly claimed. Task 5 owns this check.
4. A newly supported harness must not write Papercuts records into another client's journal or alter existing journals. Task 4 owns this check.
5. New executable metadata and version surfaces must participate in validation, release synchronization, and CI change detection. Tasks 2 and 3 own this check.

## Cohort 0: support contract and complete packages

### Task 1: Define honest support records and package checks

**Files:**

- Create `docs/compatibility.md` as the maintained support/evidence matrix.
- Modify `docs/plugin-development.md`, `README.md`, and `plugins/README.md` to explain the matrix and link verified installation instructions.
- Extend `tests/validate_marketplaces.test.js` and `scripts/validate_marketplaces.js` only for a concrete package-containment/reference regression not already covered.

**Contract:** Each support row records host/surface, exact version, plugin/component, installation route, evidence date, result (`documented`, `source-checked`, `verified`, or `unsupported`), and limitations. Initial new-host rows remain documented/source-checked.

- [x] Record existing support separately from the new candidate hosts; never upgrade historical Codex/Claude checks without fresh evidence.
- [x] Check the complete relocated Copywriter and Agent Doctor package references. Assert that Copywriter's sibling `write/` resources and packaged renderers remain reachable under the relocated plugin root.
- [x] Document full-package installation as required for those packages. Skill-only copying is eligible only after it proves all required resources remain available.
- [x] Retain local execution of code-simplifier/PR Review Toolkit on targets without native specialist agents.
- [x] Run the relevant existing root checks. Publish no new support badges yet.

**Done:** A contributor can distinguish discovery from behavior and knows the package boundary each install must preserve.

## Cohort 1: native plugin consumers

### Task 2: Add eligible catalogs and released-host discovery

**Files:**

- Create `.github/plugin/marketplace.json` and `.grok-plugin/marketplace.json` only as their respective host checks succeed.
- Modify `scripts/validate_marketplaces.js`, `tests/validate_marketplaces.test.js`, `AGENTS.md`, and `docs/plugin-development.md` for the newly supported native catalog roles.
- Modify plugin READMEs for eligible verified components; do not add native plugin manifests merely to satisfy another client's conventions.

**Consumes:** Task 1's component-level support records and intact plugin packages.

**Produces:** Hand-maintained native catalog entries referencing the same package directories. Initial workflow candidates are eli5, code-simplifier, pr-review-toolkit, and copywriter, one plugin addition at a time.

- [x] In isolated environments, prove direct/local installation and reference resolution before adding each remote catalog entry.
- [x] Check Copilot CLI independently. Inspect the selected manifest and the actual active skill source, including same-name shadowing. VS Code Local and VS Code Copilot were removed from scope by the user.
- [x] Check Grok's released manifest selection against the source finding. Prove adding a fallback native manifest does not override root `plugin.json`; test the actual selected configuration when adding components.
- [x] Add focused validator fixtures for each newly supported catalog shape, exact source path, and missing selected package. Preserve existing catalog tests and ordering policy.
- [x] Update the repository's two-catalog description deliberately; retain its no-generation/no-payload-duplication rules. Run `npm test` and `npm run validate`.

**Done:** Each promoted catalog installs an eligible intact package in its named released host. Agent Doctor, automatic hooks, and Papercuts are not implicitly promoted with the core workflows.

## Cohort 2: skill paths and native extension packaging

### Task 3: Add OpenCode and Pi distribution routes

**Files:**

- Create host-specific instructions under `docs/installation/` for OpenCode and Pi as each route is verified.
- Modify root `package.json` with an explicit `pi` resources field only if repository-root Pi Git installation is selected and tested.
- Modify `scripts/version_plugins.js` and `tests/version_plugins.test.js` when a version-bearing manifest is added.
- Modify `scripts/plugin_ci.js` and `tests/plugin_ci.test.js` when executable adapters introduce another scripted surface.

**Contract:** Registration always points into an intact installed checkout/package. Keep host metadata beside the shared payload; no generated export trees.

- [x] Verify OpenCode v1.19.3 or a later explicitly selected release with absolute `skills.paths` entries. Read actual Copywriter parent resources; do not use `skills.urls` as an untested substitute for package installation.
- [x] Verify Pi v1.3.0 or a later explicitly selected release with a root `pi.skills` selection of eligible paths. Test local per-plugin installation as an alternative, resource filtering, and absence of nested dependency/build requirements.
- [x] Inspect Pi's production dependency-install behavior and document it accurately. Do not add runtime dependencies or install hooks just for packaging.
- [x] For each added version surface, extend the existing synchronization test to show automatic patch updates and rejection of mismatched explicit versions. Do not synchronize private contributor package versions unless they become actual release identities.
- [x] Ensure adapter-only changes select the owning plugin's checks. Preserve the current shared-contract change behavior.
- [x] Run relevant existing root checks and update only verified distribution/skill rows.

**Done:** These hosts can find and invoke eligible skills with intact package resources. No hook or tool parity is implied.

## Cohort 3: application tools and automatic policy

### Task 4: Expand Papercuts one host at a time

**Files:**

- Modify `plugins/papercuts/src/paths.js`, `src/cli.js`, and `src/mcp_server.js` only where their current client contract requires it.
- Update `plugins/papercuts/skills/papercuts/SKILL.md`, its referenced storage guidance, README, and selected native MCP metadata together.
- Extend existing `plugins/papercuts/tests/papercuts.test.js` and `tests/mcp.test.js` fixtures.
- Rebuild the committed `plugins/papercuts/dist/mcp_server.js` using its existing build workflow; preserve bundled license evidence.

**Contract:** An explicit supported client identifier selects a fixed per-client user journal. Existing `codex` and `claude` selection, paths, error behavior, and data remain unchanged. Agree and document the first new client's user-journal location before coding; do not guess host home-variable semantics or add configurable storage.

- [x] Start with Copilot. Establish a loading route that actually exposes `dist/mcp_server.js`, including root-versus-native manifest precedence. Choose the smallest proven native/catalog configuration rather than unconditionally restoring the portable schema.
- [x] Add one focused client/storage regression: explicit new client wins over a conflicting environment default, resolves its documented user journal, and leaves existing client journals untouched. Preserve invalid-client rejection.
- [x] Extend the existing offline bundled-MCP case for that client: initialize, list tools, lodge/list synthetic data in a temporary home, and check client attribution/storage.
- [x] Verify the same behavior through the real host's MCP tools from a relocated package. Set `project_root` to the active workspace, never the plugin directory.
- [x] Add OpenCode, Pi, and Grok individually using the same evidence gate. Pi should use native MCP registration, not a third-party bridge; OpenCode should use its native MCP transport, not duplicated tools.
- [x] Run Papercuts' existing test/validation entrypoints and root checks after relevant changes. Promote tools separately from automatic lodging.

**Done per host:** The bundled server is discoverable and performs a real isolated complaint round trip with correct storage. Skill discovery alone is insufficient.

### Task 5: Add automatic instructions where a real context API exists

**Files:**

- Extend existing hook scripts or add minimal host-specific entrypoints inside `plugins/read-the-room/` and `plugins/papercuts/`.
- Add native host hook/extension metadata beside those plugins as needed.
- Extend `plugins/read-the-room/tests/session_start.test.js` and `plugins/papercuts/tests/session_start.test.js`; update their existing test/validation entrypoints for all new executable files.

**Contract:** Canonical instructions remain the existing skill and reference files. Adapters handle host event/input/output details. Extract shared text construction only when needed by a real second entrypoint; do not create a generic lifecycle framework.

- [x] First adapt Copilot startup output to its documented top-level context contract. Test the exact envelope and real first-response policy delivery; preserve Codex/Claude hook output.
- VS Code Local and VS Code Copilot policy, reminder, MCP, and lifecycle acceptance are excluded from this iteration. Earlier desktop observations remain historical evidence only.
- [x] For OpenCode, use the pinned native system-transform API and test compaction retention. For Pi, use `before_agent_start` context without replacing unrelated system instructions.
- [x] Check the claimed native lifecycle transitions: Copilot CLI startup, second prompt, resume, and manual compaction; OpenCode startup, second prompt, resume, and compaction; Pi startup, second prompt, compaction, and disk-backed resume. Inspect model-visible policy, not merely exit status or stdout. Additional workflow/provider combinations remain unverified.
- [x] Keep Grok manual-only unless a released native mechanism demonstrably supplies policy before the first response. A passive startup hook that ignores stdout is not an implementation candidate for equivalent behavior.
- [x] Run affected existing plugin suites and root checks. Record automatic-policy status independently of the corresponding MCP tools.

**Done per host:** Automatic policy delivery is observed without explicitly invoking the skill, at every lifecycle point the support record promises.

## Cohort 4: selective host features and publication

### Task 6: Scope Agent Doctor and native agents deliberately

**Files:**

- Modify the relevant `plugins/agent-doctor/skills/` descriptions, provider references, analyzer, and existing tests only for separately selected host coverage.
- Add native specialist definitions to code-simplifier/PR Review Toolkit only when that host's delegation is a demonstrated requirement.

- [x] Make unsupported-current-client behavior explicit before advertising Agent Doctor in a new-host catalog. Portable package inspection can be offered separately from settings or usage inspection.
- Deferred: add host configuration references only with verified precedence rules and a bounded read scope. Add a session-history parser only after documenting the actual versioned format and meaningful load-evidence fixtures; do not count mentions as use.
- [x] Retain the specialist local fallback by default. If native agents are added, verify prompt equivalence, tool availability, permission boundaries, actual delegation, and version/validation coverage.

**Done:** Each advertised Agent Doctor function or specialist role has its own evidence; an install badge does not imply all functions work.

### Task 7: Investigate Cascade skills after core cohorts

**Files:** Host installation documentation, selected plugin adapters, and their existing validation/test entrypoints as justified by actual demand.

- [x] Defer Cascade runtime verification: no exact installed Windsurf/Devin Desktop product/version was verified in the checked standard application locations. No support claim is made, as allowed by this task’s completion condition.
- Deferred with Cascade: reuse existing MCP services where available. Avoid another catalog, runtime bridge, or export format merely to increase a badge count.

**Done:** Windsurf / Devin Desktop has a verified skills-only route, or is explicitly deferred without a support claim.

### Task 8: Release verified support without expanding CI unnecessarily

**Files:** `docs/compatibility.md`, affected plugin READMEs, root documentation, and `.github/workflows/validate.yml` only when a new required check exists.

- [x] Record host versions and sanitized discovery/behavior evidence in the support matrix. Link detailed instructions; keep unsupported components visible.
- [x] Keep deterministic package/adapter checks in normal CI. Use a separate opt-in/manual job or documented isolated run for authenticated host behavior; unavailable credentials produce an unverified result, not a pass.
- [x] Run `npm test`, `npm run validate`, and every changed scripted plugin's required entrypoints. Existing Codex/Claude loader, MCP, and relocated hook evidence is recorded in the execution record. Publication is outside this execution; fresh authenticated legacy model behavior remains a release limitation.
- [x] Apply the existing release-version policy to all introduced release identities. Add badges or installation promises only for verified rows.

**Done:** A release communicates exactly which host, version, component, and installation route were checked.

## Recommended first implementation slice

Complete Tasks 1 and 2 for **eli5 on Copilot**, then repeat for Grok. This isolates distribution and discovery with the simplest package. Add the other core workflows one at a time, explicitly checking Copywriter's complete resources. Start Papercuts and automatic-policy work only after those routes are reliable. OpenCode and Pi remain the next native packaging cohort, not blocked on optional native agents or Agent Doctor telemetry. Windsurf / Devin Desktop remains a later skills-only investigation.

No universal installer, manifest compiler, payload fork, new dependency, bulk catalog generator, or blanket compatibility badge is planned.
