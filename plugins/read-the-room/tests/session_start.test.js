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

test('packaged hook loads current guidance from any directory for each configured session source', (t) => {
  const { root, plugin, skill } = fixture(t);
  const config = JSON.parse(readFileSync(resolve(plugin, 'hooks/hooks.json'), 'utf8'));
  const group = config.hooks.SessionStart[0];
  assert.equal(group.matcher, 'startup|resume|clear|compact');
  const matcher = new RegExp(group.matcher);
  assert.equal(group.hooks[0].timeout, 5);
  assert.equal(group.hooks[0].async, undefined);
  assert.equal(group.hooks[0].statusMessage, 'Loading Read the Room writing guidance...');
  for (const [source, rootVariable] of [['startup','CLAUDE_PLUGIN_ROOT'], ['resume','CLAUDE_PLUGIN_ROOT'], ['clear','CLAUDE_PLUGIN_ROOT'], ['compact','CLAUDE_PLUGIN_ROOT'], ['startup','PLUGIN_ROOT']]) {
    assert.equal(matcher.test(source), true);
    if (source === 'compact') appendFileSync(resolve(skill, 'SKILL.md'), '\nFresh policy after compaction.\n');
    const result = spawnSync(group.hooks[0].command, {
      shell: true, cwd: root, env: { ...process.env, PLUGIN_ROOT: '', CLAUDE_PLUGIN_ROOT: '', [rootVariable]: plugin },
      input: JSON.stringify({ hook_event_name: 'SessionStart', source }), encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout).hookSpecificOutput;
    assert.equal(output.hookEventName, 'SessionStart');
    const context = output.additionalContext;
    assert.ok(context.startsWith(`Resolve relative references against this skill directory: <${skill}>\n\n`));
    assert.equal(context.split(skill).length - 1, 1);
    assert.ok(context.includes('# Make It Make Sense'));
    assert.ok(context.includes('Drafting does not authorize posting'));
    assert.ok(context.includes('This startup block includes only the writing policy and agent-response guide.'));
    assert.ok(!context.includes('name: make-it-make-sense'));
    for (const name of ['agent-responses', 'version-control', 'issue-trackers', 'knowledge-bases', 'chat', 'sources']) {
      const path = resolve(skill, `references/${name}.md`);
      assert.ok(context.includes(`](references/${name}.md)`));
      assert.equal(context.includes(readFileSync(path, 'utf8').trim()), name === 'agent-responses');
    }
    if (source === 'compact') assert.ok(context.includes('Fresh policy after compaction.'));
  }
});

test('packaged prompt hook repeats a short reminder with all channel references', (t) => {
  const { root, plugin, skill } = fixture(t);
  const config = JSON.parse(readFileSync(resolve(plugin, 'hooks/hooks.json'), 'utf8'));
  const group = config.hooks.UserPromptSubmit[0];
  assert.equal(group.matcher, undefined);
  assert.equal(group.hooks[0].timeout, 5);
  assert.equal(group.hooks[0].async, undefined);
  let previous;
  for (const [prompt, rootVariable] of [['Draft a pull request description.','CLAUDE_PLUGIN_ROOT'], ['Now write a chat reply.','PLUGIN_ROOT']]) {
    const result = spawnSync(group.hooks[0].command, {
      shell: true, cwd: root, env: { ...process.env, PLUGIN_ROOT: '', CLAUDE_PLUGIN_ROOT: '', [rootVariable]: plugin },
      input: JSON.stringify({ hook_event_name: 'UserPromptSubmit', prompt }), encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout).hookSpecificOutput;
    assert.equal(output.hookEventName, 'UserPromptSubmit');
    const context = output.additionalContext;
    assert.ok(context.includes(resolve(skill, 'references')));
    assert.ok(context.includes('Before drafting or editing'));
    assert.ok(context.includes('already in active context'));
    assert.ok(context.includes('pull requests and merge requests (PRs/MRs)'));
    assert.ok(context.length < 1200);
    for (const name of ['agent-responses', 'version-control', 'issue-trackers', 'knowledge-bases', 'chat']) {
      assert.ok(context.includes(`${name}.md`));
      assert.ok(!context.includes(readFileSync(resolve(skill, `references/${name}.md`), 'utf8').trim()));
    }
    assert.ok(!context.includes('sources.md'));
    if (previous) assert.equal(context, previous);
    previous = context;
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

test('OpenCode adapters preserve host context and reload current policy', async t => {
  const { plugin, skill } = fixture(t);
  const { default: extension } = await import(require('node:url').pathToFileURL(resolve(plugin,'scripts/opencode.mjs')));
  const hooks = await extension();
  const output = { system: ['Existing host instructions'] };
  await hooks['experimental.chat.system.transform']({},output);
  assert.equal(output.system[0],'Existing host instructions');
  assert.ok(output.system[1].includes('# Make It Make Sense'));
  assert.ok(output.system[1].includes(skill));
  appendFileSync(resolve(skill,'SKILL.md'),'\nUpdated installed policy.\n');
  const compacted = { context: ['Existing summary'] };
  await hooks['experimental.session.compacting']({},compacted);
  assert.equal(compacted.context[0],'Existing summary');
  assert.ok(compacted.context[1].includes('Updated installed policy.'));
});

test('Pi adapter owns one system section without replacing host instructions', async t => {
  const { plugin, skill } = fixture(t);
  const { default: extension } = await import(require('node:url').pathToFileURL(resolve(plugin,'scripts/pi.mjs')));
  const handlers = new Map();
  extension({ on: (event, handler) => handlers.set(event,handler) });
  const event = { systemPromptOptions: { sections: { existing: 'Existing host instructions' } } };
  await handlers.get('before_agent_start')(event);
  assert.equal(event.systemPromptOptions.sections.existing,'Existing host instructions');
  assert.ok(event.systemPromptOptions.sections['read-the-room'].includes('# Make It Make Sense'));
  appendFileSync(resolve(skill,'SKILL.md'),'\nUpdated installed policy.\n');
  await handlers.get('before_agent_start')(event);
  assert.ok(event.systemPromptOptions.sections['read-the-room'].includes('Updated installed policy.'));
  assert.equal(Object.keys(event.systemPromptOptions.sections).length,2);
});

test('Copilot startup emits its native top-level context envelope', t => {
  const { plugin } = fixture(t);
  const native = JSON.parse(readFileSync(resolve(plugin,'.plugin/plugin.json'),'utf8'));
  const config = JSON.parse(readFileSync(resolve(plugin,native.hooks),'utf8'));
  assert.equal(config.version,1);
  const result = spawnSync(config.hooks.sessionStart[0].command,{shell:true,env:{...process.env,PLUGIN_ROOT:plugin},encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const output = JSON.parse(result.stdout);
  assert.ok(output.additionalContext?.includes('# Make It Make Sense'));
  assert.equal(output.hookSpecificOutput,undefined);
});
