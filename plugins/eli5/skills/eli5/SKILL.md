---
name: eli5
description: Use for $eli5, 'explain like I’m five', beginner explanations, or simple visual explanations of an unfamiliar topic.
---

# eli5

Explain the user's topic to a beginner through a visual HTML explainer with one concrete analogy and few words. Keep the mechanism accurate, define essential terms, and make clear where the analogy stops matching reality. Ask for a topic only if none is available in the request or context.

## Output

- If the user requests plain text or another format, honor that choice.
- Otherwise, use an available in-chat HTML visualization or artifact capability. When the Visualize skill is available, read it and follow its rendering and delivery contract. Keep the visual in the rendered surface and any accompanying prose brief.
- Without an inline renderer, create a standalone `<topic>.html` file in an authorized workspace output directory. Return a clickable link and one sentence describing the explainer; do not dump the HTML into the conversation or terminal.
- Use a small Markdown diagram or labeled sequence only when neither inline rendering nor file creation is available. State that limitation briefly.

## Explain visually

Make one large, clearly labeled visual carry the explanation. Show the mechanism as a short sequence or a changing scene, with brief captions that connect the analogy to the real topic. Use interaction only when it teaches something: for example, stepping through a DNS lookup or adjusting an input to see its effect. Avoid decorative controls and long prose sections.

Keep layouts readable on narrow screens. Use labeled native controls, keyboard access, sufficient contrast, text alternatives for visuals, and reduced-motion support when animating. Meaning must not depend on color alone.

## Standalone HTML

Use a complete HTML document with a title, viewport metadata, embedded CSS, and only the JavaScript needed for the explanation. Prefer HTML and inline SVG with system fonts. The file must work directly in a browser without network requests, external libraries, a build step, or a server. Do not require another plugin or scaffold an app.

Read the saved file back before delivery. When browser inspection is available, check the layout at a narrow width and exercise any controls; report any unverified behavior without claiming it was tested.
