'use strict';

const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');

function sessionContext() {
  const skill = resolve(__dirname, '../skills/make-it-make-sense');
  const read = (path) => new TextDecoder('utf-8', { fatal: true }).decode(readFileSync(path));
  const lines = read(resolve(skill, 'SKILL.md')).split(/\r?\n/);
  const end = lines.indexOf('---', 1);
  if (lines[0] !== '---' || end === -1) throw new Error('SKILL.md must have YAML frontmatter');
  const body = lines.slice(end + 1).join('\n').trim();
  const guide = read(resolve(skill, 'references/agent-responses.md')).trim();
  if (!body || !guide) throw new Error('Writing policy and agent-response guide must not be empty');
  return `Resolve relative references against this skill directory: <${skill}>\n\nThis startup block includes only the writing policy and agent-response guide. Read the matching channel reference before drafting or editing other artifacts unless already in active context.\n\n${body}\n\n${guide}`;
}
module.exports = { sessionContext };
