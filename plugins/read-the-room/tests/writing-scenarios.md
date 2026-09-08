# Writing policy checks

Use these fixed prompts when changing the writing policy. Compare the previous and proposed policy with the relevant channel guide under the same model and conditions, preferably in separate fresh contexts. Inspect outputs against the criteria rather than requiring exact wording. A small qualitative check does not establish reliability across models or sessions.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Beginner explanation | Explain idempotency to someone new to APIs in two or three sentences. | Explain the term accurately with a concrete example; distinguish repeated effects from identical responses; use connected, natural prose. |
| Technical review | Draft a blocking review finding: the retry loop resets the deadline, so the total operation can exceed the timeout. No tests were run. | State the finding, impact, blocking status, and requested correction; preserve the verification limit without inventing code locations or results. |
| Uncertain diagnosis | Summarize: restarting restored service; the cause is unknown; caching is only a hypothesis. | Separate the observed recovery from the unconfirmed cause; no claim that the restart fixed the root cause. |
| Procedure | Write instructions from these facts: set API_TOKEN to the token for the target account; run `client status`; expected output is `connected`; stop if the result is `unauthorized`. | Preserve exact literals, sequence, expected result, and stopping condition; direct actions with no invented setup. |

Across all scenarios, check that brevity preserves necessary information, terminology stays consistent, and the voice remains respectful. For future compression, compare the actual startup payload size as well as the outputs. Automated tests cover hook loading and package validity, not these writing judgments.

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
