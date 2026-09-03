# Read the Room

Help coding agents shape clear communication for the human and channel in front of them.

Read the Room packages a shared human-facing communication contract as one portable skill. [`skills/make-it-make-sense/SKILL.md`](skills/make-it-make-sense/SKILL.md) is the canonical policy. Channel references contain only the rules specific to each artifact.

The `make-it-make-sense` skill covers:

- Human-readable agent updates, questions, plans, findings, blockers, and final answers
- Commit messages, pull and merge requests, reviews, and discussion replies
- Issue tracker titles, descriptions, acceptance criteria, comments, and status updates
- Wiki and knowledge-base pages, READMEs, runbooks, decision records, code comments, and durable documentation
- Chat messages, announcements, status updates, and thread replies

The skill description exposes the technical communication, channel, and artifact terms used for automatic discovery. Once active, the skill directs the agent to read only the relevant channel reference. Automatic selection remains host-controlled and may not activate for every underlying task, especially after context compaction. Invoke `make-it-make-sense` explicitly, or require it in host-level instructions, when the policy must apply to a response or existing draft.

Skills guide the agent's writing; they do not intercept outgoing messages. Drafting an external artifact does not authorize posting it, changing workflow state, or resolving a discussion.
