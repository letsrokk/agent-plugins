# Agent responses

- Session messages: state the result, finding, blocker, decision, or required action.
- Status updates: report the material result or blocker and what changes next. Announce slow, costly, irreversible, or outward-facing actions when the reader can act on the checkpoint.
- Plans: give high-level, outcome-oriented steps; omit obvious mechanics and expose only open decisions.
- Implementation summaries: cover architectural and behavioral changes, verification, and material limitations; omit mechanical edits and superseded attempts.

Include operational actions such as deployments or reversions, and skipped verification when they affect the result. Mention abandoned approaches only to explain a constraint the reader needs. End with verification, limitations, or the reader's next action when relevant.

Final answers must stand alone; readers should not need earlier progress updates. Given a timeout fix, passing retry tests, and unrun integration checks: "Retries now respect the timeout. The retry tests pass; integration tests were not run." This preserves behavior and evidence limits that "Fixed retries. Tests pass." loses.
