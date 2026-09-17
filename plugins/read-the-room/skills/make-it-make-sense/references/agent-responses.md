# Agent responses

- Session messages: state the result, finding, blocker, decision, or required action.
- Status updates: report the material result or blocker and what changes next. Announce slow, costly, irreversible, or outward-facing actions when the reader can act on the checkpoint.
- Plans: give high-level, outcome-oriented steps; omit obvious mechanics and expose only open decisions.
- Implementation summaries: cover architectural and behavioral changes, verification, and material limitations; omit mechanical edits and superseded attempts.

Include operational actions such as deployments or reversions, and skipped verification when they affect the result. Mention abandoned approaches only to explain a constraint the reader needs. End with verification, limitations, or the reader's next action when relevant.

When work remains, distinguish what the agent will do from what requires the user. Continue authorized work with available tools; request a user action only when their input or access is necessary. For instructions the user must execute, give ordered actions and the known expected result. When the task is complete, stop without inventing another task.

Report an error's observed failure and known cause. When the cause is unknown, say so and name the next diagnostic step instead of presenting a hypothesis as the fix. For example, given only an HTTP 401 failure: "The integration test received 401 instead of 200; the cause is unknown. I'll inspect the request and authentication setup next." Use that next action only when inspection is authorized and available; do not ask the user to run checks the agent can run.

## Final task outputs

Final answers must stand alone; readers must not need earlier progress updates. Keep the handoff as short as possible without compromising clarity, precision, or necessary evidence.

- Lead with one sentence stating the outcome or blocker. Include the PR or artifact link there when it is the deliverable; omit preambles and closing pleasantries.
- Use bullets for multiple independent facts. Separate changed behavior, verification, and limitations instead of packing them into a paragraph. A simple outcome that fits clearly in one or two sentences needs no list or headings.
- For longer handoffs covering multiple categories, require short headings such as Changes, Verification, and Remaining. Include only categories with useful information; use brief prose where connected reasoning is necessary.
- Keep one point per bullet and put consequential information first. Group long lists by topic; never hide failures or requested findings to meet a length or item limit.
- End with a next action only when needed, and name whether the agent or user owns it. Continue authorized work instead of turning it into instructions for the user. Completed work needs no invitation or invented follow-up.

For example, given a timeout fix, a cancellation fix, passing focused tests, and unrun integration checks:

> Fixed retry timeout and cancellation handling.
>
> **Changes**
>
> - Retry attempts share the original deadline.
> - Cancellation stops pending retries.
>
> **Verification**
>
> - Retry and cancellation tests passed.
> - Integration tests were not run.
