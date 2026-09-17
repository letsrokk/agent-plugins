# eli5

Make unfamiliar topics easier to understand with a concrete analogy, simple visuals, and few words.

```text
$eli5 how does DNS work
```

Produces a visual HTML explainer with big pictures, one concrete analogy, and very few words for someone who knows nothing about the topic. Adds interaction when it helps explain how something works.

Uses an in-chat visualization or artifact capability when available. Otherwise, saves a self-contained `.html` file and links to it so you can open it in a browser. Standalone explainers work offline without dependencies or a server. Plain-text requests are honored; Markdown is the fallback when rendering and file creation are both unavailable.

Ported for Codex from Anthropic's [eli5 plugin](https://github.com/anthropics/claude-plugins-community/tree/main/eli5), authored by Thariq Shihipar.
