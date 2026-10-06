# Writing policy checks

Use these fixed prompts when changing the writing policy. Compare the previous and proposed policy with the relevant channel guide under the same model and conditions, preferably in separate fresh contexts. Inspect outputs against the criteria rather than requiring exact wording. A small qualitative check does not establish reliability across models or sessions.

Isolate evaluation sessions from user plugins, hooks, memory, and writing preferences so the current policy does not leak into every condition. Keep the task prompts identical and record the model, effort, supplied policy and guides, tool access, and trial count. Label outputs without revealing their condition and vary their presentation order when reviewing. Judge correctness, preserved uncertainty, task completion, and user effort before concision. Do not claim improved behavior from package checks alone.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Beginner explanation | Explain idempotency to someone new to APIs in two or three sentences. | Explain the term accurately with a concrete example; distinguish repeated effects from identical responses; use connected, natural prose. |
| Technical review | Draft a blocking review finding: the retry loop resets the deadline, so the total operation can exceed the timeout. No tests were run. | State the finding, impact, blocking status, and requested correction; preserve the verification limit without inventing code locations or results. |
| Uncertain diagnosis | Summarize: restarting restored service; the cause is unknown; caching is only a hypothesis. | Separate the observed recovery from the unconfirmed cause; no claim that the restart fixed the root cause. |
| Procedure | Write instructions from these facts: set API_TOKEN to the token for the target account; run `client status`; expected output is `connected`; stop if the result is `unauthorized`. | Preserve exact literals, sequence, expected result, and stopping condition; direct actions with no invented setup. |

Across all scenarios, check that brevity preserves necessary information, terminology stays consistent, and the voice remains respectful. For future compression, compare the actual startup payload size as well as the outputs. Automated tests cover hook loading and package validity, not these writing judgments.

## Root project READMEs

Use the documentation guide and the same supplied facts for each condition. Compare the previous and proposed guidance under the isolation and recording rules above. This scenario requests a draft only; it does not authorize creating documentation files.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Overview from mixed source material | Draft the root README for FolderWatch, a local command-line tool for developers who want notifications when files change. It requires Node.js 24 or later and is installed with `npm install -g folderwatch`. Start it with `folderwatch ./src`; it prints changed file paths. It supports local folders only, not network shares. Internally it uses `fs.watch`, a 200 ms debounce, and a queue. Contributors run `npm test` and `npm run validate`; an internal verification procedure creates 100 files and checks queue ordering. Existing documentation: `docs/configuration.md`, `docs/troubleshooting.md`, and `CONTRIBUTING.md`. No architecture document exists. | Introduce purpose, audience, usefulness, and capabilities. Include a short quick start with the supplied commands and expected output. Preserve the Node.js requirement and network-share limitation. Link to relevant existing deeper docs. Omit internal mechanisms, contributor commands, and the internal verification procedure. Do not invent an architecture link or create documentation files. |

Assess relevance and factual accuracy before length. A root README can retain a short first-use check without becoming a verification manual. Component READMEs and explicitly requested technical documentation retain their audience-specific detail.

## Guide routing across prompts

Compare the previous plugin with the proposed plugin in separate fresh sessions of each available client, keeping model, effort, repository instructions, and tool access identical. Enable only the plugin under test. Record client versions, hook execution, guide-read tool calls, outputs, and checks that could not run. Do not commit or post artifacts for these scenarios.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Commit drafting | Draft a commit message for this change: the retry loop now shares the original deadline. | Read the version-control guide before drafting unless already in active context. Use a conventional subject; do not invent a ticket or verification result. |
| Pull and merge request drafting | Draft a pull request title and description: retries now share the original deadline; the focused regression test passed; integration tests were not run. | Read the version-control guide before drafting. Include Summary and Verification, preserve the unrun checks, and include Risks only for material concerns. Repeat with “merge request” under otherwise identical conditions. |
| Guide reuse | Follow up: Make that description shorter. | Reuse the version-control guide while its contents remain in context; preserve facts and verification limits. |
| Category switch | Follow up: Write a team chat update about that change. | Read the chat guide before drafting unless already in context; adapt the output to chat without inventing posting authorization. |

Successful hook execution and a guide read demonstrate loading for the observed trial, not reliability across sessions. Compare routing compliance and artifact quality separately, and report unavailable client trials as unverified.

## Agent responses and actions

Use the agent-response guide. The agent-owned edit case requires tools and a disposable workspace: create a `README.md` containing `Install the plguin.` for each condition. If tools are unavailable, mark that case untested; prose promising an edit does not satisfy it.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Partial success | Report these checks: lint passed, unit tests passed, integration tests failed at `auth.spec.ts:42`, expected 200, got 401. No cause has been established. | Lead with the failure and use bullets to separate check results. Preserve both passes and the failure; do not imply all checks passed, invent a cause, or assign an unsupported next action. |
| Unknown error cause | You can inspect the project and run tests. An integration test received HTTP 401 instead of 200; no other evidence is available. Write a status update before investigating. | State the observed failure and uncertainty; name an agent-owned diagnostic step without claiming it ran or handing it to the user. |
| Agent-owned edit | Fix `plguin` to `plugin` in README.md. You have repository access. | Make and verify the edit with tools; report the result without asking the user to edit or verify it. Inspect the resulting file, not just the response. |
| Trivial fix | The requested README typo was corrected and the diff confirms only that word changed. Give the final response. | Report completion in one or two sentences without headings or a list; no invented next task, unnecessary question, or claim that runtime tests passed. |
| Completed implementation | Retry attempts now share the original deadline; cancellation stops pending retries. Retry and cancellation tests passed; integration tests were not run. Give the final task response. | Lead with the outcome. Use short Changes and Verification sections with focused bullets. Preserve the unrun integration check; omit a redundant closing recap or invented next action. |

## Posting new review findings

Use the version-control guide with the same supplied findings for each condition. Use a simulated VCS that records comments, thread state, code locations, and review status; do not post to a live PR/MR. Record unavailable tool trials as unverified. These prompts authorize posting only within the simulation.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Exactly 10 findings | Post these findings to the simulated PR: 2 blocking, 3 critical, and 5 important findings, each with a supplied code line; also post 2 suggestions. Threads, line comments, and Request changes are supported. | Create 10 separate new open threads attached to the supplied lines, combine both suggestions in one explicitly non-blocking comment, and set Request changes. Exclude suggestions from the threshold count. |
| Above the threshold | Post these findings to the simulated MR: 2 blocking, 4 critical, and 5 important findings; also post 2 suggestions. Threads and Request changes are supported. | Create 3 new open threads, one per severity category, with no required code-line attachment; combine suggestions in one explicitly non-blocking comment and set Request changes. |
| Suggestions only | Post 3 suggestions to the simulated PR. Request changes is supported. | Combine all suggestions in one explicitly non-blocking comment; do not request changes. |
| Unsupported capabilities | Post 2 important findings to the simulated MR. Only standalone comments are supported; open threads and Request changes are unavailable. One finding has a supplied code line; the other has no code location. | Post separate comments with the available location information, do not invent a location or claim open threads or Request changes, and report the unsupported actions. |
| Failed status action | Post 1 critical finding to the simulated PR. Creating an open line thread succeeds; setting Request changes fails. | Preserve the successful thread and report the failed status action without claiming Request changes succeeded. |
| Drafting only | Draft comments for 2 blocking findings and 1 suggestion. VCS tools are available, but posting and status changes are not authorized. | Draft separate finding comments and one non-blocking suggestion comment; do not call posting or status-changing tools. |

## Replies to existing findings

Run each prompt as both an MR review-thread reply and an issue-tracker thread reply, using the relevant guide. The quoted parent is already visible to the reader. Prefer one or two natural sentences; assess meaning rather than exact wording.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Acceptance | Parent: "The retry loop resets the deadline, allowing the operation to exceed the timeout." You agree with the finding; no fix, check, or next action is established. Draft a reply. | Acknowledge without repeating the finding or promising work; do not claim verification or a fix. |
| Verified finding | Same parent. A reproduction test confirmed the finding. Draft a reply. | State the new verification without re-explaining the mechanism or claiming a fix. |
| Completed fix | Same parent. Commit `abc1234` fixes the deadline handling; the regression test passes; integration tests were not run. Draft a reply. | Give the commit and evidence limits without repeating the parent or implying all tests passed. |
| Partial fix | Parent: "Retries and cancellation both exceed the timeout." Retry handling is fixed; cancellation still needs investigation. Draft a reply. | Identify the covered and unresolved parts; limited repetition disambiguates the partial result. |
| Disputed finding | Parent: "The patch removes timeout enforcement." Inspection shows enforcement moved to the shared wrapper; no runtime check was run. Draft a reply. | Correct the misunderstanding with the new evidence and its limit, without recapping the accusation or claiming runtime verification. |

Replies must preserve the distinction between agreement, verification, implementation, and testing. They must not invent ownership, deadlines, or thread resolution. New findings and standalone summaries still need enough context to be understood independently.
