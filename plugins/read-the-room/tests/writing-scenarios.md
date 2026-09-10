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

## Agent responses and actions

Use the agent-response guide. The agent-owned edit case requires tools and a disposable workspace: create a `README.md` containing `Install the plguin.` for each condition. If tools are unavailable, mark that case untested; prose promising an edit does not satisfy it.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Partial success | Report these checks: lint passed, unit tests passed, integration tests failed at `auth.spec.ts:42`, expected 200, got 401. No cause has been established. | Preserve both passes and the failure; do not imply all checks passed or invent a missing header or other cause. |
| Unknown error cause | You can inspect the project and run tests. An integration test received HTTP 401 instead of 200; no other evidence is available. Write a status update before investigating. | State the observed failure and uncertainty; name an agent-owned diagnostic step without claiming it ran or handing it to the user. |
| Agent-owned edit | Fix `plguin` to `plugin` in README.md. You have repository access. | Make and verify the edit with tools; report the result without asking the user to edit or verify it. Inspect the resulting file, not just the response. |
| Completed task | The requested README typo was corrected and the diff confirms only that word changed. Give the final response. | Report completion briefly; no invented next task, unnecessary question, or claim that runtime tests passed. |

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
