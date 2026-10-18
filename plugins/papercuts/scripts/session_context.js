import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export function sessionContext() {
  const policy = new TextDecoder('utf-8', { fatal: true }).decode(
    readFileSync(new URL('../skills/papercuts/SKILL.md', import.meta.url)),
  );
  const lines = policy.split(/\r?\n/);
  const end = lines.indexOf('---', 1);
  if (lines[0] !== '---' || end === -1) throw new Error('SKILL.md must have YAML frontmatter');
  const body = lines.slice(end + 1).join('\n').trim();
  if (!body) throw new Error('SKILL.md must contain instructions');
  return `Resolve relative references against this skill directory: <${fileURLToPath(new URL('../skills/papercuts', import.meta.url))}>\n\n${body}`;
}
