# Version control

Use the contract for the requested artifact:

- **Commit:** Use a conventional single-line subject. Apply a required ticket prefix when repository instructions or the branch establish one. Add a body only for context a future maintainer cannot recover from the diff.
- **Pull or merge request title:** State the delivered outcome in the repository's established form. Keep required ticket prefixes exact.
- **Pull or merge request description:** Present what changed, why it changed, verification evidence, and material risks or areas reviewers should inspect. Build the account from completed work, actions taken, and resulting behavior.
- **Review comment:** Lead with the finding or requested change. Give precise evidence, impact, and the reason for the request. When reporting a response to feedback, state the action taken and its result. State whether the finding blocks. Use a plain approval when there is no finding.
- **Discussion reply:** Answer the point in the discussion that raised it. Report the decision, evidence, fix, or remaining blocker. Reply in the same discussion when following up on your own comment, confirming a finding, or reporting that a change landed. Start a new discussion only for a new, unrelated conversation. Resolve the discussion only when the point is settled and the current authorization permits it.

Omit unperformed work, abandoned approaches, and commit-by-commit history. Include a rejected approach only when it directly affects the delivered outcome or explains a constraint the reader could otherwise hit. Material skipped checks and limitations still belong when the reader needs them. Scope claims to their evidence: a focused test proves its covered path, not every related behavior. Do not invent tests, ticket references, risks, ownership, or results. Drafting text does not authorize posting it, changing review state, or resolving a discussion.
