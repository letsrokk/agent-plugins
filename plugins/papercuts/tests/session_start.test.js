import assert from 'node:assert/strict';
import { test } from 'node:test';
import { appendFileSync, cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const pluginRoot = fileURLToPath(new URL('..', import.meta.url));
function fixture(t) {
  const root = realpathSync(mkdtempSync(resolve(tmpdir(), 'papercuts hook ')));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const plugin = resolve(root, 'installed plugin');
  for (const directory of ['hooks', 'skills', '.plugin']) cpSync(resolve(pluginRoot, directory), resolve(plugin, directory), { recursive: true });
  cpSync(resolve(pluginRoot, 'scripts'), resolve(plugin, 'scripts'), { recursive: true });
  cpSync(resolve(pluginRoot, 'package.json'), resolve(plugin, 'package.json'));
  const home = resolve(root, 'home');
  mkdirSync(home);
  return { root, plugin, home, policy: resolve(plugin, 'skills/papercuts/SKILL.md') };
}

test('packaged hook injects canonical workflow for each configured session source without storage writes', (t) => {
  const { root, plugin, home, policy } = fixture(t);
  const config = JSON.parse(readFileSync(resolve(plugin, 'hooks/hooks.json'), 'utf8'));
  assert.deepEqual(config, { hooks: { SessionStart: [{ matcher: 'startup|resume|clear|compact', hooks: [{
    type: 'command', command: "node -e \"require((process.env.PLUGIN_ROOT || process.env.CLAUDE_PLUGIN_ROOT) + '/scripts/session_start.js')\"",
    timeout: 5, statusMessage: 'Loading Papercuts instructions...',
  }] }] } });
  const matcher = new RegExp(config.hooks.SessionStart[0].matcher);
  for (const [source, rootVariable] of [['startup','CLAUDE_PLUGIN_ROOT'], ['resume','CLAUDE_PLUGIN_ROOT'], ['clear','CLAUDE_PLUGIN_ROOT'], ['compact','CLAUDE_PLUGIN_ROOT'], ['startup','PLUGIN_ROOT']]) {
    assert.equal(matcher.test(source), true);
    if (source === 'compact') appendFileSync(policy, '\nFresh instructions after compaction.\n');
    const result = spawnSync(config.hooks.SessionStart[0].hooks[0].command, {
      shell: true, cwd: root,
      env: { ...process.env, HOME: home, PLUGIN_ROOT: '', CLAUDE_PLUGIN_ROOT: '', [rootVariable]: plugin },
      input: JSON.stringify({ hook_event_name: 'SessionStart', source }), encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stderr, '');
    const output = JSON.parse(result.stdout).hookSpecificOutput;
    assert.equal(output.hookEventName, 'SessionStart');
    const context = output.additionalContext;
    const canonicalBody = readFileSync(policy, 'utf8').split('---\n').slice(2).join('---\n').trim();
    const skill = resolve(plugin, 'skills/papercuts');
    assert.ok(context.startsWith(`Resolve relative references against this skill directory: <${skill}>\n\n`));
    assert.equal(context.split(skill).length - 1, 1);
    assert.ok(context.endsWith(canonicalBody));
    for (const name of ['evidence', 'maintenance']) {
      assert.ok(context.includes(`](references/${name}.md)`));
      assert.ok(!context.includes(readFileSync(resolve(skill, `references/${name}.md`), 'utf8').trim()));
    }
    for (const instruction of ['material', 'limit: 5', 'vote_for_complaint', 'lodge_complaint', "active workspace's absolute root", 'Continue the active task silently', 'Never submit secrets', 'Resolve only when verified evidence', 'reopen only when verified evidence', 'exact preview plan ID']) {
      assert.ok(context.includes(instruction), instruction);
    }
    assert.ok(!context.includes('name: papercuts'));
    assert.deepEqual(readdirSync(home), []);
    if (source === 'compact') assert.ok(context.includes('Fresh instructions after compaction.'));
  }
});

test('missing or invalid instructions emit no partial context', async (t) => {
  for (const scenario of ['missing', 'no frontmatter', 'unclosed frontmatter', 'empty body', 'invalid utf8']) {
    await t.test(scenario, (t) => {
      const { plugin, policy } = fixture(t);
      if (scenario === 'missing') rmSync(policy);
      if (scenario === 'no frontmatter') writeFileSync(policy, '# Instructions');
      if (scenario === 'unclosed frontmatter') writeFileSync(policy, '---\nname: papercuts\n# Instructions');
      if (scenario === 'empty body') writeFileSync(policy, '---\nname: papercuts\n---\n');
      if (scenario === 'invalid utf8') writeFileSync(policy, Buffer.from([0xff]));
      const result = spawnSync(process.execPath, [resolve(plugin, 'scripts/session_start.js')], { encoding: 'utf8' });
      assert.notEqual(result.status, 0);
      assert.equal(result.stdout, '');
      assert.match(result.stderr, /could not load its instructions/);
    });
  }
});

test('Copilot native hook emits workflow context without touching storage', t => {
  const { root, plugin, home } = fixture(t);
  const native = JSON.parse(readFileSync(resolve(plugin,'.plugin/plugin.json'),'utf8'));
  const config = JSON.parse(readFileSync(resolve(plugin,native.hooks),'utf8'));
  const result = spawnSync(config.hooks.sessionStart[0].command, {
    shell:true,cwd:root,env:{...process.env,HOME:home,PLUGIN_ROOT:plugin},encoding:'utf8',
  });
  assert.equal(result.status,0,result.stderr);
  const output = JSON.parse(result.stdout);
  assert.ok(output.additionalContext?.includes('lodge_complaint'));
  assert.equal(output.hookSpecificOutput,undefined);
  assert.deepEqual(readdirSync(home),[]);
});


test('native adapters preserve host policy and register the relocated Pi service', async t => {
  const { plugin, policy } = fixture(t);
  const { default: piExtension } = await import(pathToFileURL(resolve(plugin, 'scripts/pi.mjs')));
  const handlers = new Map();
  let registration;
  piExtension({
    registerMcpServer: (name, config) => { registration = { name, config }; },
    on: (event, handler) => handlers.set(event, handler),
  });
  assert.deepEqual(registration, {
    name: 'papercuts',
    config: {
      command: 'node', args: [resolve(plugin, 'dist/mcp_server.js')],
      env: { PAPERCUTS_CLIENT: 'pi' }, exposure: 'direct',
    },
  });
  const event = { systemPromptOptions: { sections: { existing: 'Host policy' } } };
  handlers.get('before_agent_start')(event);
  assert.equal(event.systemPromptOptions.sections.existing, 'Host policy');
  assert.ok(event.systemPromptOptions.sections.papercuts.includes('lodge_complaint'));
  const { default: openCodeExtension } = await import(pathToFileURL(resolve(plugin, 'scripts/opencode.mjs')));
  const hooks = await openCodeExtension();
  const output = { system: ['Host policy'] };
  await hooks['experimental.chat.system.transform']({}, output);
  assert.equal(output.system[0], 'Host policy');
  assert.equal(output.system[1], event.systemPromptOptions.sections.papercuts);
  appendFileSync(policy, '\nUpdated installed workflow.\n');
  handlers.get('before_agent_start')(event);
  const compacted = { context: ['Host summary'] };
  await hooks['experimental.session.compacting']({}, compacted);
  assert.equal(compacted.context[0], 'Host summary');
  assert.ok(compacted.context[1].includes('Updated installed workflow.'));
  assert.equal(compacted.context[1], event.systemPromptOptions.sections.papercuts);
  assert.deepEqual(Object.keys(event.systemPromptOptions.sections).sort(), ['existing', 'papercuts']);
});
