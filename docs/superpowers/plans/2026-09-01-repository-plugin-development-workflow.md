# Repository Plugin Development Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give contributors one repository-owned Codex plugin creation and local-development contract, and make the marketplace validator reject packages that violate it.

**Architecture:** Keep the Agent Plugins v1 root `plugin.json` as the portable package manifest and treat `.codex-plugin/plugin.json` as the Codex compatibility manifest for discovery, MCP configuration, and UI metadata. Extend the existing dependency-free validator to reconcile the two manifests for every Codex catalog entry, then document the complete create, validate, locally reinstall, reload, and release workflow in one guide linked from the existing repository instructions.

**Tech Stack:** Python 3.11 standard library, `unittest`, JSON manifests, Markdown, Codex plugin CLI.

**Spec:** Papercuts complaint `pc_461cadf9007a3f8c` in `.codex/papercuts.jsonl`.

## Global Constraints

- Preserve the two native catalogs and shared `plugins/` tree described in `AGENTS.md`.
- Keep `plugins/<plugin-name>/plugin.json` as the Agent Plugins v1 portable manifest.
- Require `.codex-plugin/plugin.json` only for plugins listed in `.agents/plugins/marketplace.json` and `.claude-plugin/plugin.json` only for plugins listed in `.claude-plugin/marketplace.json`.
- Keep catalog sources exactly `./plugins/<plugin-name>` and keep all plugin, directory, manifest, and catalog names aligned.
- Use Python 3.11 or later and add no dependencies.
- Add at most one new main-path test and one new critical-failure test.
- Do not change the installed system `plugin-creator` skill, generate either marketplace catalog, or add a second development plugin payload.
- Do not resolve Papercuts complaint `pc_461cadf9007a3f8c` until the new tests and repository validation pass.

## Scope and Definition of Done

The fix covers this repository's contribution and local-development workflow. It does not change Codex caching, marketplace identity rules, or the globally installed `plugin-creator` skill. The work is complete when the checked-in guide explains those external constraints, the validator enforces the repository's dual-manifest contract, existing plugins pass, the full test suite passes, and the complaint is resolved with the verification evidence.

## File Structure

- Create `docs/plugin-development.md`: the single contributor guide for manifest roles, component placement, local development, stable reinstalls, reload boundaries, and releases.
- Modify `README.md`: replace the abbreviated creation checklist with a link to the contributor guide while keeping installation instructions concise.
- Modify `plugins/README.md`: state the package layout and manifest precedence without duplicating the full workflow.
- Modify `AGENTS.md`: make the root and client compatibility manifest requirements explicit for future agents.
- Modify `scripts/validate_marketplaces.py`: require and reconcile Codex compatibility manifests for Codex catalog entries.
- Modify `tests/test_validate_marketplaces.py`: provide valid dual-manifest fixtures and prove the new success and failure behavior.

---

### Task 1: Enforce the Codex dual-manifest contract

**Files:**
- Modify: `tests/test_validate_marketplaces.py:24-299`
- Modify: `scripts/validate_marketplaces.py:21-373`

**Interfaces:**
- Consumes: the Codex catalog entry name, `plugins/<name>/plugin.json`, the on-disk `skills/` directory, and `plugins/<name>/.codex-plugin/plugin.json`.
- Produces: `_validate_portable_manifest(...) -> dict[str, Any] | None`, `_validate_codex_manifest(root: Path, name: str, portable_manifest: dict[str, Any], errors: list[str]) -> None`, and the existing `validate_repository(root: Path) -> list[str]` with additional actionable errors.

- [ ] **Step 1: Make the test fixtures represent a valid Codex package**

Add a helper that writes a compatibility manifest with the same name and version as the portable manifest:

```python
def _write_codex_manifest(
    self,
    name: str,
    *,
    version: str = "0.1.0",
    skills: bool = True,
) -> None:
    payload: dict[str, object] = {"name": name, "version": version}
    if skills:
        payload["skills"] = "./skills/"
    self._write_json(f"plugins/{name}/.codex-plugin/plugin.json", payload)
```

Give `_write_portable_manifest` a default `version` of `0.1.0`. Update existing Codex fixtures that are meant to be otherwise valid to write the compatibility manifest, including `_write_code_simplifier_package`. Do not add compatibility files to fixtures whose subject is a missing plugin directory or missing portable manifest.

- [ ] **Step 2: Add one main-path test and one critical-failure test**

The main-path test must create a generic skill package with matching portable and Codex manifests and assert that validation succeeds:

```python
def test_accepts_codex_package_with_matching_compatibility_manifest(self) -> None:
    self._write_catalogs(codex_plugins=[self._codex_entry("complete")])
    self._write_portable_manifest("complete")
    self._write_codex_manifest("complete")
    self._write_skill("complete", "complete")

    self.assertEqual(validate_repository(self.root), [])
```

The critical-failure test must use one deliberately inconsistent compatibility manifest and assert every contract error that matters: catalog-name mismatch, portable-version mismatch, and missing `./skills/` discovery declaration for an on-disk skill:

```python
def test_rejects_inconsistent_codex_compatibility_manifest(self) -> None:
    self._write_catalogs(codex_plugins=[self._codex_entry("inconsistent")])
    self._write_portable_manifest("inconsistent", version="1.2.3")
    self._write_json(
        "plugins/inconsistent/.codex-plugin/plugin.json",
        {"name": "other", "version": "1.2.2"},
    )
    self._write_skill("inconsistent", "inconsistent")

    errors = validate_repository(self.root)

    self.assertTrue(any("name must match catalog entry 'inconsistent'" in error for error in errors))
    self.assertTrue(any("version must match portable manifest '1.2.3'" in error for error in errors))
    self.assertTrue(any("skills must be './skills/'" in error for error in errors))
```

Keep missing-manifest handling in the same validator path and do not add a third test. That branch reuses `_load_json` and the explicit error pattern already exercised by `test_rejects_claude_plugin_without_compatibility_manifest`; the critical Codex regression here is a present but contradictory manifest.

- [ ] **Step 3: Run the focused tests and confirm the new assertions fail**

Run:

```sh
python3 -m unittest \
  tests.test_validate_marketplaces.MarketplaceValidationTests.test_accepts_codex_package_with_matching_compatibility_manifest \
  tests.test_validate_marketplaces.MarketplaceValidationTests.test_rejects_inconsistent_codex_compatibility_manifest -v
```

Expected: at least the inconsistent-manifest test fails because the validator does not read `.codex-plugin/plugin.json`; the main-path test may also fail until compatibility-manifest support is wired into the catalog path.

- [ ] **Step 4: Return the portable manifest from its validator**

Change the signature to:

```python
def _validate_portable_manifest(
    root: Path,
    name: str,
    catalog: Path,
    errors: list[str],
) -> dict[str, Any] | None:
```

Return `None` after load failure. For a loaded manifest, require `version` to be a non-empty string, retain all existing metadata, component, license, and package-specific checks, then return the manifest even when errors were appended. Returning the parsed object lets client-specific validation compare shared identity without loading the file twice.

- [ ] **Step 5: Add Codex compatibility-manifest validation**

Implement:

```python
def _validate_codex_manifest(
    root: Path,
    name: str,
    portable_manifest: dict[str, Any],
    errors: list[str],
) -> None:
```

The function must load `plugins/<name>/.codex-plugin/plugin.json` and emit an explicit "missing Codex compatibility manifest" error when absent. For a loaded object, require:

- `name` equals the catalog entry name.
- `version` equals the portable manifest's non-empty string `version`.
- When `plugins/<name>/skills/` contains at least one `SKILL.md`, `skills` equals `./skills/`.
- When no discoverable skill exists, reject a stray `skills` key rather than claiming a component that is not present.

Do not try to infer or generically validate `mcpServers` from `mcp.json`: Codex MCP launch configuration is client-specific in this repository, and Papercuts intentionally defines it only in the Codex compatibility manifest.

- [ ] **Step 6: Invoke client validation from the catalog path**

Add `require_codex_manifest: bool = False` beside `require_claude_manifest` in `_validate_plugins`. Capture the portable result once:

```python
portable_manifest = _validate_portable_manifest(root, name, catalog_path, errors)
if require_codex_manifest and portable_manifest is not None:
    _validate_codex_manifest(root, name, portable_manifest, errors)
if require_claude_manifest:
    _validate_claude_manifest(root, name, errors)
```

Pass `require_codex_manifest=True` from `_validate_codex_catalog`. Keep the Claude path unchanged.

- [ ] **Step 7: Run the focused tests and the whole validator suite**

Run:

```sh
python3 -m unittest \
  tests.test_validate_marketplaces.MarketplaceValidationTests.test_accepts_codex_package_with_matching_compatibility_manifest \
  tests.test_validate_marketplaces.MarketplaceValidationTests.test_rejects_inconsistent_codex_compatibility_manifest -v
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
```

Expected: both focused tests pass, all existing tests pass, and the three current Codex plugins validate without manifest or version errors.

- [ ] **Step 8: Commit the executable contract**

```sh
git add scripts/validate_marketplaces.py tests/test_validate_marketplaces.py
git commit -m "fix: validate Codex compatibility manifests"
```

### Task 2: Publish one repository-owned development guide

**Files:**
- Create: `docs/plugin-development.md`
- Modify: `README.md:21-29`
- Modify: `plugins/README.md:3-12`
- Modify: `AGENTS.md:8-18`

**Interfaces:**
- Consumes: the manifest and catalog rules enforced by Task 1 and the current `codex plugin marketplace add`, `codex plugin add`, and `codex plugin list` commands.
- Produces: one contributor workflow linked from the root README, with compact package rules retained in `plugins/README.md` and agent-enforceable rules retained in `AGENTS.md`.

- [ ] **Step 1: Create the authoritative guide with explicit manifest roles**

Create `docs/plugin-development.md` with these sections and decisions:

```markdown
# Plugin development

## Manifest roles

| File | Role |
| --- | --- |
| `plugins/<name>/plugin.json` | Portable Agent Plugins v1 identity and shared package metadata. It must not contain Codex-only `skills`, `mcpServers`, or `interface` fields. |
| `plugins/<name>/.codex-plugin/plugin.json` | Required for Codex catalog entries. It declares Codex discovery routes, MCP launch configuration, and UI metadata. Its `name` and `version` must match the portable manifest. |
| `plugins/<name>/.claude-plugin/plugin.json` | Required only for Claude Code catalog entries. It contains Claude Code-specific metadata and MCP launch configuration. |
```

State that portable skills live under `skills/<skill-name>/SKILL.md`, Codex custom agents live under `skills/<skill-name>/agents/<agent_name>.toml`, portable MCP configuration may use `mcp.json`, and client launch details remain in compatibility manifests when required.

- [ ] **Step 2: Document the creation and release checklist**

Include an ordered checklist that requires contributors to:

1. Create `plugins/<name>/plugin.json` with a release version.
2. Add at least one discoverable component.
3. Add the compatibility manifest for each target catalog.
4. Keep the portable and Codex `name` and `version` equal.
5. Add catalog entries with exact `./plugins/<name>` sources.
6. Run both repository validation commands.
7. Remove any `+codex.local-*` suffix before a release commit.

Do not duplicate the full JSON manifests; point to one current plugin package as an example so the examples cannot silently become a second contract.

- [ ] **Step 3: Document the local-development and stable-reinstall loop**

Record the constraints before the commands:

- A configured marketplace name is its identity; the Git marketplace and local worktree cannot coexist under the same top-level marketplace name.
- A plugin name is its install identity; local development replaces the stable installation unless the developer creates a genuinely separate plugin identity.
- Use a disposable development worktree whose local Codex marketplace name is `rokk-club-codex-plugins-dev`, and never commit that local catalog-name change.
- For each local iteration, set the same build-metadata version in both the portable and Codex manifests, for example `0.2.0+codex.local-20260901-140000`.
- Reinstall after each meaningful change, then start a new Codex task so skills and MCP tools reload.

Include the exact loop:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
codex plugin marketplace add /absolute/path/to/agent-plugins-dev
codex plugin add <plugin-name>@rokk-club-codex-plugins-dev
codex plugin list
```

Then state: test in a new Codex task; return to the stable build with `codex plugin add <plugin-name>@rokk-club-codex-plugins`; do not edit an installed cache copy.

- [ ] **Step 4: Make existing documentation point to the guide**

Update `README.md` so its "Add a plugin" section links to `docs/plugin-development.md` and retains only the five-line overview. Update `plugins/README.md` to describe all three manifest roles and link to the full workflow. Update `AGENTS.md` to require `.codex-plugin/plugin.json` for Codex-listed plugins, require its name/version to match the portable manifest, and name `docs/plugin-development.md` as the workflow authority.

Avoid copying the local-development command sequence into all three files; the new guide owns it.

- [ ] **Step 5: Check the guide against the executable contract**

Read the three real package layouts:

```sh
find plugins/code-simplifier plugins/eli5 plugins/papercuts \
  -maxdepth 3 -type f -print | sort
```

Confirm every documented rule matches at least one current package and no current package contradicts the guide. Run:

```sh
rg -n "plugin.json|codex-plugin|claude-plugin|cachebuster|new Codex task|marketplace" \
  README.md plugins/README.md AGENTS.md docs/plugin-development.md
```

Expected: the full workflow appears only in `docs/plugin-development.md`; the other files state their local contract and link to it.

- [ ] **Step 6: Commit the guide and links**

```sh
git add README.md plugins/README.md AGENTS.md docs/plugin-development.md
git commit -m "docs: define repository plugin development workflow"
```

### Task 3: Verify the fix and close the complaint

**Files:**
- Inspect: `docs/plugin-development.md`
- Inspect: `scripts/validate_marketplaces.py`
- Inspect: `tests/test_validate_marketplaces.py`
- Update after verification: `.codex/papercuts.jsonl` through Papercuts, not by hand

**Interfaces:**
- Consumes: the completed guide, validator, tests, and complaint `pc_461cadf9007a3f8c`.
- Produces: fresh verification evidence and a resolved Papercuts record that names that evidence.

- [ ] **Step 1: Confirm the documented CLI surface is still current**

Run these read-only checks:

```sh
codex plugin marketplace add --help
codex plugin add --help
codex plugin list
```

Expected: local paths remain accepted marketplace sources, `PLUGIN@MARKETPLACE` remains the install selector, and the list command remains available. If any command has changed, correct only the affected guide text before continuing.

- [ ] **Step 2: Run final repository verification**

Run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_marketplaces.py
git diff --check
git status --short
```

Expected: all tests pass; marketplace validation prints `Marketplace validation passed.`; `git diff --check` prints nothing; status contains only the intended commits plus the pre-existing local `.codex/` journal.

- [ ] **Step 3: Review against the complaint acceptance criteria**

Confirm all six points directly:

- One checked-in guide owns the repository-marketplace workflow.
- Root and client manifest precedence is explicit.
- The validator enforces Codex manifest presence, identity, version alignment, and skill discovery.
- The guide explains local versus stable marketplace and plugin identities.
- The guide explains cachebuster version alignment and reinstall steps.
- The guide requires a new Codex task after reinstall.

Do not resolve the complaint if any point is absent or only implied.

- [ ] **Step 4: Resolve the Papercuts record with verification evidence**

Use the Papercuts skill with project root `/Users/rokk/Projects/github/ai/agent-plugins`, or the project CLI fallback:

```sh
plugins/papercuts/scripts/papercuts resolve pc_461cadf9007a3f8c \
  --note "docs/plugin-development.md now defines manifest precedence, local/stable identities, cachebuster reinstall steps, and the new-task reload boundary. The validator enforces matching Codex compatibility manifests; the full unittest suite and scripts/validate_marketplaces.py pass."
```

If the sandbox blocks `.codex/papercuts.jsonl`, request approval for this single journal update. Do not edit the JSONL file directly.

- [ ] **Step 5: Record the final verification commit if resolution caused no tracked changes**

The Papercuts journal is local project state, not repository content. Do not add `.codex/papercuts.jsonl` to Git. If Tasks 1 and 2 are already committed and `git status --short` shows no additional tracked changes, create no empty commit.

## Self-Review

- Spec coverage: all complaint clauses map to Task 1 validator behavior, Task 2 guide sections, or Task 3 verification and resolution.
- Placeholder scan: every implementation and test step contains exact behavior, signatures, commands, and expected results.
- Type consistency: `_validate_portable_manifest` returns the dictionary consumed by `_validate_codex_manifest`; `_validate_plugins` passes the same object only for Codex entries.
- Scope check: the plan changes one repository workflow and its validator. It does not modify Codex itself, the global plugin creator, marketplace generation, or plugin runtime behavior.
