'use strict';

const assert = require('node:assert/strict');
const { test } = require('node:test');
const { appendFileSync, cpSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');

function fixture(t) {
  const root = realpathSync(mkdtempSync(resolve(tmpdir(), 'read the room ')));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const plugin = resolve(root, 'installed plugin');
  cpSync(resolve(__dirname, '..'), plugin, { recursive: true });
  return { root, plugin, skill: resolve(plugin, 'skills/make-it-make-sense') };
}

test('packaged hook loads current guidance from any directory and session source', (t) => {
  const { root, plugin, skill } = fixture(t);
  const config = JSON.parse(readFileSync(resolve(plugin, 'hooks/hooks.json'), 'utf8'));
  const group = config.hooks.SessionStart[0];
  assert.equal(group.matcher, undefined);
  assert.equal(group.hooks[0].timeout, 5);
  assert.equal(group.hooks[0].async, undefined);
  assert.equal(group.hooks[0].statusMessage, 'Loading Read the Room writing guidance...');
  for (const source of ['startup', 'resume', 'clear', 'compact']) {
    if (source === 'compact') appendFileSync(resolve(skill, 'SKILL.md'), '\nFresh policy after compaction.\n');
    const result = spawnSync(group.hooks[0].command, {
      shell: true, cwd: root, env: { ...process.env, CLAUDE_PLUGIN_ROOT: plugin },
      input: JSON.stringify({ hook_event_name: 'SessionStart', source }), encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout).hookSpecificOutput;
    assert.equal(output.hookEventName, 'SessionStart');
    const context = output.additionalContext;
    assert.ok(context.includes('# Make It Make Sense'));
    assert.ok(context.includes('Drafting does not authorize posting'));
    assert.ok(!context.includes('name: make-it-make-sense'));
    for (const name of ['agent-responses', 'version-control', 'issue-trackers', 'knowledge-bases', 'chat']) {
      const path = resolve(skill, `references/${name}.md`);
      assert.ok(context.includes(`](<${path}>)`));
      assert.equal(context.includes(readFileSync(path, 'utf8').trim()), name === 'agent-responses');
    }
    if (source === 'compact') assert.ok(context.includes('Fresh policy after compaction.'));
  }
});

test('missing or invalid policy files emit no partial context', async (t) => {
  for (const scenario of ['missing skill', 'missing guide', 'no frontmatter', 'unclosed frontmatter', 'empty body', 'empty guide', 'invalid utf8']) {
    await t.test(scenario, (t) => {
      const { plugin, skill } = fixture(t);
      const policy = resolve(skill, 'SKILL.md');
      const guide = resolve(skill, 'references/agent-responses.md');
      if (scenario === 'missing skill') rmSync(policy);
      if (scenario === 'missing guide') rmSync(guide);
      if (scenario === 'no frontmatter') writeFileSync(policy, '# Policy');
      if (scenario === 'unclosed frontmatter') writeFileSync(policy, '---\nname: writing\n# Policy');
      if (scenario === 'empty body') writeFileSync(policy, '---\nname: writing\n---\n');
      if (scenario === 'empty guide') writeFileSync(guide, '');
      if (scenario === 'invalid utf8') writeFileSync(policy, Buffer.from([0xff]));
      const result = spawnSync(process.execPath, [resolve(plugin, 'scripts/session_start.js')], { encoding: 'utf8' });
      assert.notEqual(result.status, 0);
      assert.equal(result.stdout, '');
      assert.match(result.stderr, /could not load its writing policy/);
    });
  }
});
