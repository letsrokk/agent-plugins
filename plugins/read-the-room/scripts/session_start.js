#!/usr/bin/env node
'use strict';

const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');

try {
  const skill = resolve(__dirname, '../skills/make-it-make-sense');
  const read = (path) => new TextDecoder('utf-8', { fatal: true }).decode(readFileSync(path));
  const lines = read(resolve(skill, 'SKILL.md')).split(/\r?\n/);
  const end = lines.indexOf('---', 1);
  if (lines[0] !== '---' || end === -1) throw new Error('SKILL.md must have YAML frontmatter');
  const body = lines.slice(end + 1).join('\n').trim().replace(
    /\]\((references\/[^)]+)\)/g,
    (_, reference) => `](<${resolve(skill, reference)}>)`,
  );
  const guide = read(resolve(skill, 'references/agent-responses.md')).trim();
  if (!body || !guide) throw new Error('Writing policy and agent-response guide must not be empty');
  console.log(JSON.stringify({ hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: `${body}\n\n${guide}`,
  } }));
} catch (error) {
  console.error(`read-the-room could not load its writing policy: ${error.message}`);
  process.exitCode = 1;
}
