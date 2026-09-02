# Read the Room

Help coding agents shape clear communication for the human and channel in front of them.

Read the Room packages the communication principles in the repository maintainer's user-level `AGENTS.md` as one portable skill. The complete shared style lives in one place, while channel references add only the rules specific to each artifact.

The `make-it-make-sense` skill covers:

- Human-readable agent updates, questions, plans, findings, blockers, and final answers
- Commit messages, pull and merge requests, reviews, and discussion replies
- Issue tracker titles, descriptions, acceptance criteria, comments, and status updates
- Wiki and knowledge-base pages, READMEs, runbooks, decision records, code comments, and durable documentation
- Chat messages, announcements, status updates, and thread replies

The skill description exposes the channel and artifact keywords needed for automatic discovery. Once active, the skill loads only the relevant channel reference. Name the skill explicitly when you need deterministic routing or want to revise an existing draft.

Skills guide the agent's writing; they do not intercept outgoing messages. Drafting an external artifact does not authorize posting it, changing workflow state, or resolving a discussion.
