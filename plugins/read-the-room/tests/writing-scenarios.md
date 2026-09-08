# Writing policy checks

Use these fixed prompts when changing the writing policy. Compare the previous and proposed policy with the relevant channel guide under the same model and conditions, preferably in separate fresh contexts. Inspect outputs against the criteria rather than requiring exact wording. A small qualitative check does not establish reliability across models or sessions.

| Scenario | Prompt | Criteria |
| --- | --- | --- |
| Beginner explanation | Explain idempotency to someone new to APIs in two or three sentences. | Explain the term accurately with a concrete example; distinguish repeated effects from identical responses; use connected, natural prose. |
| Technical review | Draft a blocking review finding: the retry loop resets the deadline, so the total operation can exceed the timeout. No tests were run. | State the finding, impact, blocking status, and requested correction; preserve the verification limit without inventing code locations or results. |
| Uncertain diagnosis | Summarize: restarting restored service; the cause is unknown; caching is only a hypothesis. | Separate the observed recovery from the unconfirmed cause; no claim that the restart fixed the root cause. |
| Procedure | Write instructions from these facts: set API_TOKEN to the token for the target account; run `client status`; expected output is `connected`; stop if the result is `unauthorized`. | Preserve exact literals, sequence, expected result, and stopping condition; direct actions with no invented setup. |

Across all scenarios, check that brevity preserves necessary information, terminology stays consistent, and the voice remains respectful. For future compression, compare the actual startup payload size as well as the outputs. Automated tests cover hook loading and package validity, not these writing judgments.
