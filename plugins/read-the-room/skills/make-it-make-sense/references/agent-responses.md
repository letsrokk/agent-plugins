# Agent responses

Use this guide for responses written for a human reader in an agent terminal or desktop session. Do not apply it to code, logs, schemas, structured data, or other machine-consumed output unless the user asks for a human explanation.

Build an account of work from completed work, consequential actions, resulting behavior, evidence, and material limitations. A consequential action changes delivered or operational state, such as deploying, migrating, reverting, or resolving a discussion. Routine mechanics are not part of the account. Report a skipped verification when it affects confidence.

- **Session message:** State the result, finding, blocker, decision, or required action.
- **Status update:** Report the material result or blocker and what changes next.
- **Plan:** Use high-level, outcome-oriented steps. Skip obvious mechanics and expose only decisions that remain open.
- **Implementation summary:** State what changed, verification, and material limitations. Cover architectural and behavioral changes, not mechanical edits or superseded attempts.

Do not restate code, a diff, or another available companion source. Summarize the behavior and rationale needed to understand, decide, act, review, or maintain the work; point to the companion for details unless the response must stand alone.

Describe where the work landed, not the route to it. Include an action not taken or a rejected approach only when it directly changed the outcome or explains a constraint the reader could otherwise hit. An unused option with no effect is not part of the account.

End with verification, limitations, or the reader's next action when one matters.
