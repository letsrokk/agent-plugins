#!/usr/bin/env node
import { readFileSync } from 'node:fs';

try {
  const policy = new TextDecoder('utf-8', { fatal: true }).decode(
    readFileSync(new URL('../skills/papercuts/SKILL.md', import.meta.url)),
  );
  const lines = policy.split(/\r?\n/);
  const end = lines.indexOf('---', 1);
  if (lines[0] !== '---' || end === -1) throw new Error('SKILL.md must have YAML frontmatter');
  const body = lines.slice(end + 1).join('\n').trim();
  if (!body) throw new Error('SKILL.md must contain instructions');
  console.log(JSON.stringify({ hookSpecificOutput: {
    hookEventName: 'SessionStart',
    additionalContext: body,
  } }));
} catch (error) {
  console.error(`papercuts could not load its instructions: ${error.message}`);
  process.exitCode = 1;
}
