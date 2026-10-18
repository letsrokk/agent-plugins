# Rokk Club Agent Plugins

Give your coding agent more ways to help: review a change, make sense of its settings, explain an unfamiliar topic, or shape an engaging piece of writing.

Rokk Club brings these workflows to your coding agent as plugins you can install individually. Browse the collection below and choose the ones that fit your work.

![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg)

[Compatibility matrix](docs/compatibility.md) · [Plugin development](docs/plugin-development.md)

Copilot CLI, Grok Build, OpenCode, and Pi routes are experimental. Scripted workflows require Node.js 24 or later on your agent’s `PATH`.

## Connect your agent

Add the marketplace or register this checkout, then choose the plugins you want. Replace `<plugin>` with a supported plugin name before running the commands. For the experimental routes, use a complete checkout containing these integrations and replace `/absolute/path/agent-plugins` with its location.

<details>
<summary><strong>Codex</strong> · marketplace</summary>

Run in your terminal:

```sh
codex plugin marketplace add letsrokk/agent-plugins
codex plugin add "<plugin>@rokk-club-codex-plugins"
```

Replace `<plugin>` with a supported plugin name below. For Papercuts and Read the Room, review and trust the startup hooks in `/hooks`, then start a fresh session.

</details>

<details>
<summary><strong>Claude Code</strong> · marketplace</summary>

Run inside Claude Code:

```text
/plugin marketplace add letsrokk/agent-plugins
/plugin install <plugin>@rokk-club-claude-plugins
```

Replace `<plugin>` with a supported plugin name below, then start a fresh session.

</details>

<details>
<summary><strong>Copilot CLI</strong> · marketplace</summary>

```sh
copilot plugin marketplace add /absolute/path/agent-plugins
copilot plugin install "<plugin>@rokk-club-copilot-plugins"
copilot plugin list
copilot skill list --json
```

Inspect each skill’s `source` and `path` to confirm the intended package. Project skills take precedence over personal skills, which take precedence over plugin skills.

Use the full installed identity with `copilot plugin disable`, `enable`, `update`, or `uninstall`. Local marketplace packages load live from the checkout; `uninstall` disables the entry and retains checkout files.

</details>

<details>
<summary><strong>Grok Build</strong> · marketplace</summary>

```sh
grok plugin marketplace add /absolute/path/agent-plugins
grok plugin marketplace list
```

Use the source name printed by `marketplace list`. For a checkout registered as `agent-plugins`, review the selected package before enabling its executable capabilities with `--trust`:

```sh
grok plugin install "<plugin>@agent-plugins" --trust
grok inspect --json
```

Use `grok plugin disable NAME`, `enable NAME`, `update NAME`, or `uninstall NAME` to manage installed packages.

</details>

<details>
<summary><strong>OpenCode</strong> · skill paths and native configuration</summary>

Merge the selected plugins’ complete skill directories into your existing OpenCode configuration. These entries register the four core workflow packages:

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

Run `opencode debug skill` to confirm discovery, then explicitly request a workflow. Retain the full checkout so sibling resources and scripts stay available.

See [Read the Room setup](plugins/read-the-room/README.md#additional-harnesses) and [Papercuts setup](plugins/papercuts/README.md#additional-harnesses) for their skill paths, automatic policy extensions, and MCP configuration.

</details>

<details>
<summary><strong>Pi</strong> · local package</summary>

```sh
pi install /absolute/path/agent-plugins
pi list
```

The package registers resources in place and includes eli5, code-simplifier, pr-review-toolkit, copywriter, Read the Room, and Papercuts. Select its skills and extensions with `pi config`, and keep the checkout available.

Start an authenticated Pi session and explicitly request a selected workflow. Use `pi remove /absolute/path/agent-plugins` to unregister the package. Plugin-specific activation details are in each plugin’s README.

</details>

## Rokk Club plugins

| Plugin | What it helps with | Agents |
| --- | --- | --- |
| [papercuts](plugins/papercuts/README.md) | Keep a local record of tool failures, confusing instructions, and recurring workflow problems so you can review what keeps getting in the way. | ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |
| [agent-doctor](plugins/agent-doctor/README.md) | Inspect agent settings, plugin structure, and local skill usage. Get configuration findings and suggested fixes while leaving your files unchanged. | ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg) |
| [read-the-room](plugins/read-the-room/README.md) | Help your agent write clear updates, reviews, documentation, and chat messages suited to the reader. | ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |
| [copywriter](plugins/copywriter/README.md) | Turn source material into product copy and editable pitch decks. Shape your drafts, outlines, and notes into articles and social posts. | ![Codex](assets/agent-badges/codex.svg) ![Claude Code](assets/agent-badges/claude-code.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |

## Ports

Adapted from upstream plugins. Each package retains its attribution and license information.

| Plugin | What it helps with | Agents |
| --- | --- | --- |
| [eli5](plugins/eli5/README.md) | Make unfamiliar topics easier to understand with a concrete analogy, simple visuals, and few words. | ![Codex](assets/agent-badges/codex.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |
| [pr-review-toolkit](plugins/pr-review-toolkit/README.md) | Review pull requests and local changes for bugs, test gaps, unclear comments, error handling, and type issues. | ![Codex](assets/agent-badges/codex.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |
| [code-simplifier](plugins/code-simplifier/README.md) | Make the code you choose easier to read and maintain while preserving its behavior. | ![Codex](assets/agent-badges/codex.svg) ![Copilot CLI](assets/agent-badges/copilot-cli.svg) ![Grok Build](assets/agent-badges/grok-build.svg) ![OpenCode](assets/agent-badges/opencode.svg) ![Pi](assets/agent-badges/pi.svg) |

## Try a plugin

After installing Read the Room, ask your agent:

```text
Use make-it-make-sense to rewrite this update: "Tests pass. The migration still needs review."
```

Expect a clear update that preserves both the passing tests and the pending review. Each plugin’s README has more examples and setup details.

## Add a plugin

Have a workflow to share? Follow the [plugin development workflow](docs/plugin-development.md) for package layout, client manifests, catalog entries, and required checks. All catalogs use the same shared `plugins/` tree.

## License

This repository is available under the [MIT License](LICENSE). Individual plugins may declare a different license in their own manifests and package files.
