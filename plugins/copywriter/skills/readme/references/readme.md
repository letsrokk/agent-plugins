# README contract

Inspect the hosting platform's surfaced README rather than assuming the root README is displayed. On GitHub, `.github`, root, then `docs` is the precedence. Establish the final file location before checking relative links.

Use applicable sections only: product name/description and material maturity; reader task; compact genuine example/screenshot; prerequisites/install; first successful use with expected output; capabilities/constraints and justified alternatives; existing docs/support/contribution/license links. Put deeper reference in links rather than burying the first successful use.

For a targeted rewrite identify exact section boundaries and preserve surrounding bytes where practical. Preserve existing working links, badges, anchors, commands, APIs, attribution, and legal text unless their change is authorized and supported. Never invent `CONTRIBUTING.md`, package-manager distribution, support channels, or license terms. A public repository is not necessarily open source.

Trace install and example commands to the selected checkout or release. Distinguish executable instructions from pseudocode. Prefer a safe deterministic local example with explicit prerequisites and expected output. Read commands before execution; avoid destructive operations, deployments, lifecycle scripts, and live customer actions merely to test prose.

Verify relevant existing examples in the documented environment when safe, record actual results/environment or label unverified, resolve local links and images from the final README location, and check anchors after heading edits. Check that claims match the selected version and monorepo package. Review the final diff for unintended section changes, broken badges, attribution loss, and legal-text changes.
