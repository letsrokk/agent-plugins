# Plugin development

Repository tooling requires Node.js 24 or later. At the repository root, run `npm ci --ignore-scripts --no-audit --no-fund` to install the pinned TOML parser used to validate custom agents. Run `npm test` and `npm run validate` before committing. Plugin build dependencies remain separate and are installed from the relevant plugin directory.

## Manifest roles

Use Agent Plugins v1 as the base for shared metadata and package layout. Accept native Codex and Claude Code structures where the portable format or a client’s implementation cannot express or load a required component. Keep one shared payload and separate client configuration; portability must not disable working hooks or MCP servers.

| File | Role |
| --- | --- |
| `plugins/<name>/plugin.json` | Agent Plugins v1 identity and shared package metadata. Keep client-only `skills`, `hooks`, `mcpServers`, and `interface` fields in native manifests. Omit `$schema` when native loading is required, retaining the shared metadata. |
| `plugins/<name>/.codex-plugin/plugin.json` | Required for Codex catalog entries. It declares Codex discovery routes, MCP launch configuration, and UI metadata. Its `name` and `version` must match the portable manifest. |
| `plugins/<name>/.claude-plugin/plugin.json` | Required only for Claude Code catalog entries. It contains Claude Code-specific metadata and MCP launch configuration. |

Portable skills live under `skills/<skill-name>/SKILL.md`. Codex custom agents live under `skills/<skill-name>/agents/<agent_name>.toml`. Portable MCP configuration may use `mcp.json`; client launch details remain in compatibility manifests when required.

### Choosing portable or native loading

Keep the Agent Plugins v1 `$schema` for plugins whose components load correctly through the portable path. For a native exception, retain root `plugin.json`, provide the target client's native manifest, synchronize names and versions, and explain the exception in the plugin README. Do not add client-specific directories or catalog entries for clients the plugin does not target.

Verified with Codex CLI 0.153.4: the Agent Plugins v1 loader skips plugin hooks and reads MCP configuration from `mcp.json`, ignoring native `mcpServers` declarations. Declaring `hooks` in `.codex-plugin/plugin.json` alone does not overcome this. Papercuts and Read the Room therefore omit the root `$schema` so Codex selects native loading. Papercuts keeps its client-specific MCP launch settings in each native manifest. The validator rejects a Codex plugin combining the portable schema with native hooks or `mcpServers`. Recheck host behavior before changing this exception; see the [Codex loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs) and [portable manifest adapter](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/agent_plugin_manifest.rs).

Claude Code uses `.claude-plugin/plugin.json`, discovers `hooks/hooks.json` by default, and supports MCP configuration in its manifest or root `.mcp.json`. Do not confuse Claude's `.mcp.json` with portable `mcp.json`. Use `${CLAUDE_PLUGIN_ROOT}` for Claude launch paths; Codex native MCP settings may use plugin-relative paths and `cwd`. Keep the executable payload shared even when launch settings differ. See the [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference).

Keep each `SKILL.md` at or below 7,168 bytes to leave headroom when a host loads it into a prompt. Put only universal instructions and routing in the main file. Move task-, channel-, or artifact-specific guidance into focused files under the skill's `references/` directory, and direct the agent to read only the relevant reference. Repository validation enforces the byte limit; check a file directly with `wc -c skills/<skill-name>/SKILL.md`.

See one current plugin package, such as [`plugins/papercuts/`](../plugins/papercuts/), for the package structure. Do not copy its JSON manifests as a second contract.

## Scripted plugin contract

A plugin is scripted when its package contains any of these directories:

- `scripts/`
- `src/`
- `skills/<skill-name>/scripts/`

Every scripted plugin must provide these Node.js 24-compatible entrypoints:

- `scripts/test.js` runs the plugin's tests.
- `scripts/validate.js` runs its static and package-specific validation.

Both entrypoints take no arguments, run from the plugin root, and return zero only when the check passes. They must not prompt, depend on untracked local state, or modify tracked files. Use plain JavaScript and Node's built-in modules and test runner where sufficient.

Use this CommonJS test entrypoint for a `node:test` suite:

```js
#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const { readdirSync } = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const tests = readdirSync(path.join(root, 'tests'))
  .filter(name => name.endsWith('.test.js')).sort()
  .map(name => path.join('tests', name));
if (tests.length === 0) throw new Error('No tests found');
const result = spawnSync(process.execPath, ['--test', ...tests], {
  cwd: root,
  stdio: 'inherit',
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
```

Validation should run `node --check` on executable JavaScript and check the plugin's package contracts, including hook configuration when present. Do not scan dependencies under `node_modules/`.

Installed plugins must work with only Node.js on the noninteractive process's `PATH`. Runtime dependencies must be bundled in the plugin, with a committed lockfile and third-party license notices. Do not install dependencies or fetch code from a hook or MCP launcher. Papercuts uses npm only for contributor builds and CI: run `npm ci --ignore-scripts --no-audit --no-fund` in its plugin root before validation. Its validation checks that the committed bundle reproduces from the locked dependencies without rewriting it. Read the plugin README for its build command.

GitHub Actions runs both entrypoints on Ubuntu for each changed scripted plugin. A change to this document, the repository instructions, the marketplace validator, the plugin selector, the root package manifest or lockfile, or the validation workflow runs them for every scripted plugin. Skill-only plugins do not need these entrypoints and do not create plugin matrix jobs.

## Lifecycle hooks

Use the shared `hooks/hooks.json` default location for Codex and Claude Code. Hook commands must quote `${CLAUDE_PLUGIN_ROOT}` paths and include a short `statusMessage` describing the action. Keep startup instruction hooks synchronous and read their canonical skill policy on each invocation instead of duplicating it in the script.

Codex plugin installation does not trust hooks automatically. After installation or a hook definition change, review and trust the hook in `/hooks`, then start a fresh session. Verify context injection without explicitly invoking the skill. Never edit saved trust hashes or installed cache files. Claude Code discovers the same bundled hooks when the plugin is enabled.

## Create and release a plugin

1. Create `plugins/<name>/plugin.json` with a release version.
2. Add at least one discoverable component.
3. Add `plugins/<name>/README.md` with a short description, a usage example, and a brief explanation of the result. Follow the concise style of [eli5's README](../plugins/eli5/README.md).
4. Add the compatibility manifest for each target catalog.
5. Keep every plugin manifest version equal.
6. Add catalog entries with exact `./plugins/<name>` sources.
7. If the plugin is scripted, add and run its test and validation entrypoints.
8. Run both repository validation commands.
9. Remove any `+codex.local-*` suffix before a release commit.

Release versions on `main` use stable `MAJOR.MINOR.PATCH` SemVer. A pull request that
changes an existing plugin can leave its version unchanged; after validation succeeds on
`main`, GitHub Actions increments the patch version and synchronizes the portable, Codex,
and Claude plugin manifests that exist for that plugin. New and deleted plugins
are excluded from automatic bumps.

Set a strictly higher version in the pull request when the change needs an intentional major,
minor, or patch release. Update every existing version declaration together. Pull request
validation rejects malformed, inconsistent, or decreased versions, and the merge automation
preserves a valid higher version without adding another patch bump.

The automation commits generated bumps to `main` as `chore: bump plugin versions`. It retries
against the latest `main` when another merge wins the push race, and a newer version can cover
several changes that merged before the generated commit. The repository `GITHUB_TOKEN` does
not start another workflow run for its own commit, which prevents recursion. The automation
does not create tags, GitHub Releases, or changelogs. Branch protection must allow this
workflow's narrowly scoped `contents: write` job to update `main`.

## Local development and stable reinstall

A configured marketplace name is its identity; the Git marketplace and local worktree cannot coexist under the same top-level marketplace name. A plugin name is its install identity; local development replaces the stable installation unless the developer creates a genuinely separate plugin identity.

Use a disposable development worktree whose local Codex marketplace name is `rokk-club-codex-plugins-dev`, and never commit that local catalog-name change. Validate the repository while the stable marketplace name is present. Then change only the local worktree's top-level marketplace name to `rokk-club-codex-plugins-dev` before local registration, and restore `rokk-club-codex-plugins` before final validation or commit.

For each local iteration, set the same build-metadata version in both the portable and Codex manifests, for example `0.2.0+codex.local-20260901-140000`. Reinstall after each meaningful change, then start a new Codex task so skills and MCP tools reload.

Run the plugin entrypoints from a scripted plugin's root:

```sh
cd plugins/<plugin-name>
node scripts/test.js
node scripts/validate.js
cd ../..
```

Then run the repository checks and reinstall the plugin:

```sh
npm test
npm run validate
codex plugin marketplace add /absolute/path/to/agent-plugins-dev
codex plugin add <plugin-name>@rokk-club-codex-plugins-dev
codex plugin list
```

Test in a new Codex task. Return to the stable build with `codex plugin add <plugin-name>@rokk-club-codex-plugins`; do not edit an installed cache copy.
