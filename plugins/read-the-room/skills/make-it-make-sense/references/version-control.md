# Version control

Use the contract for the requested artifact:

- **Commit:** Use a conventional single-line subject. Apply a required ticket prefix when repository instructions or the branch establish one. Add a body only for context a future maintainer cannot recover from the diff.
- **Pull or merge request title:** State the delivered outcome in the repository's established form. Keep required ticket prefixes exact.
- **Pull or merge request description:** Present the delivered behavior, why it changed, verification evidence, and material risks or areas reviewers should inspect.
- **Review comment:** Lead with the finding or requested change. Give precise evidence, impact, and the reason for the request. When reporting a response to feedback, state the action taken and its result. State whether the finding blocks. Use a plain approval when there is no finding.
- **Discussion reply:** Answer the point raised with the decision, evidence, fix, or remaining blocker.

Before drafting a pull or merge request description, read the diff. Do not inventory changed files or methods, repeat rationale already documented in code, recount commit history, or assess the work's quality. Include rationale only when it affects review or is not recoverable from the diff.

- Bad: "`retry_request()` creates a deadline inside the loop so each retry receives the full timeout. Keeping the deadline outside the loop would let an earlier attempt consume the later attempts' time budget. The code uses a per-attempt context and cancels it before continuing, which prevents timers from accumulating."
- Good: "Retries now apply the timeout per attempt; the rationale is documented beside the loop. Focused timeout tests pass. Review cancellation behavior."

Scope verification claims to their evidence: a focused test proves its covered path, not every related behavior.
