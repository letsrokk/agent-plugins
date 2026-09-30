#!/usr/bin/env node
'use strict';

const { resolve } = require('node:path');

const references = resolve(__dirname, '../skills/make-it-make-sense/references');
console.log(JSON.stringify({ hookSpecificOutput: {
  hookEventName: 'UserPromptSubmit',
  additionalContext: `Before drafting or editing human-facing text, read and apply the matching writing guide unless its contents are already in active context. Reuse guides while present. Files are under <${references}>: responses, updates and summaries → agent-responses.md; commit messages, pull requests and merge requests (PRs/MRs), reviews and version-control discussions → version-control.md; issues and tracker comments → issue-trackers.md; documentation and code comments → knowledge-bases.md; chat messages and replies → chat.md. For mixed outputs, use each artifact's guide. Follow the user's requested content and format; preserve facts and uncertainty. Drafting does not authorize posting.`,
} }));
