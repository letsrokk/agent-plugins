# Knowledge bases and documentation

Write durable documentation that helps its intended reader complete or maintain a task without access to the original conversation. Do not invent commands, behavior, prerequisites, support claims, or operational guarantees.

1. State the document's purpose or the reader's intended outcome first.
2. Put prerequisites, constraints, and warnings before the instructions they govern.
3. Explain current behavior in present tense with consistent technical terms.
4. Give numbered steps with direct instructions, generally one action per step; keep simultaneous actions together. Explain placeholders and distinguish illustrative output from observed results. Keep required actions in steps, not notes.
5. State how the reader verifies the result and what a material failure means when that information is known.

For a README, optimize for using and maintaining the component. For a runbook, make conditions, actions, checks, and stopping points explicit. For a decision record, state the decision, its relevant context, and its consequences; include status, date, owner, or alternatives only when the source supplies them. For reference material, organize by the questions readers need to answer rather than by the order in which the information was discovered.

For a code comment, explain why non-obvious behavior or a constraint exists. Do not restate the code, narrate implementation history, or record rejected versions.

## Reader support

- Define unfamiliar terms and abbreviations on first use. Retain established technical names and searchable terminology; explain long names before using an unambiguous shorter form.
- Prefer concrete verbs: "validate the token" is clearer than "perform token validation." Keep connecting words when they establish a dependency: "After the backup completes, restart the service."
- In procedures, introduce a command by its purpose. Given a required account token, write "Set `API_TOKEN` to the token for the target account," rather than "Simply configure the appropriate credentials."
- Separate instructions from explanation. Include known expected results, failure conditions, and stopping points where they affect the task. Avoid promises about speed or ease that the evidence does not support.

## Accessible presentation

- Use descriptive, sentence-case headings in a logical hierarchy and meaningful link text. Use parallel list items and tables only when their shared fields aid comparison.
- Format identifiers and commands as code; preserve exact UI labels, normally in bold. Explain units and use unambiguous dates and times when relevant.
- Refer to controls by their labels, not color, shape, or location alone. Provide meaningful text alternatives for informative images and a text explanation of information needed to complete the task. Keep commands and output as selectable text.
- Use respectful terminology and examples without unnecessary assumptions about readers. Prefer literal wording for international documentation; explain necessary domain terms rather than silently renaming code or product identifiers.
