const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { analyze } = require('../skills/inspect-plugin-usage/scripts/inspect_sessions.js');

function setup(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'agent-doctor-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return { root, target_kind: 'plugin', target_name: 'plugin-a', project: path.join(root, 'project'), days: 30, now: new Date('2026-09-04T12:00:00Z'), codex_home: path.join(root, '.codex'), claude_home: path.join(root, '.claude') };
}
function write(file, records, prefix = '') {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, prefix + records.map(record => JSON.stringify(record) + '\n').join(''));
}
const codex = (payload, type = 'response_item', timestamp = '2026-09-03T10:00:00Z') => ({ timestamp, type, payload });
const claude = (content, extra = {}) => ({ type: 'assistant', timestamp: '2026-09-02T11:00:00Z', message: { content }, ...extra });
const skillCall = id => ({ type: 'tool_use', name: 'Skill', id, input: { skill: 'plugin-a:review' } });
const skillPath = root => `${root}/.codex/plugins/cache/market/plugin-a/1.0.0/skills/review/SKILL.md`;

test('counts recent plugin and skill usage globally and by project', async t => {
  const options = setup(t), skill = skillPath(options.root);
  write(`${options.codex_home}/sessions/current.jsonl`, [
    codex({ cwd: options.project }, 'session_meta'),
    codex({ type: 'custom_tool_call', name: 'exec', call_id: 'success', input: `sed -n '1,200p' '${skill}'` }),
    codex({ type: 'custom_tool_call_output', call_id: 'success', output: [{ type: 'input_text', text: JSON.stringify({ output: '---\nname: review\ndescription: Review code\n---\n', exit_code: 0 }) }] }, 'response_item', '2026-09-04T12:00:01Z'),
  ]);
  write(`${options.codex_home}/sessions/old.jsonl`, [
    codex({ cwd: options.project }, 'session_meta', '2026-07-01T10:00:00Z'),
    codex({ type: 'custom_tool_call', name: 'exec', call_id: 'old', input: `cat '${skill}'` }, 'response_item', '2026-07-01T10:01:00Z'),
  ]);
  write(`${options.claude_home}/projects/sample/session.jsonl`, [
    claude([skillCall('success')], { cwd: `${options.project}/src` }),
    claude([{ type: 'tool_result', tool_use_id: 'success', is_error: false }], { type: 'user', timestamp: '2026-09-04T12:00:01Z' }),
  ]);
  write(`${options.claude_home}/projects/other/session/subagents/agent-1.jsonl`, [claude('<command-name>plugin-a:review</command-name>', { type: 'user', isMeta: true, cwd: `${options.project}-other` })]);
  const report = await analyze(options);
  assert.deepEqual(report.scopes.all.combined, { attempts: 3, successful: 3, problems: 0, incomplete: 0, scanned_sessions: 3, matched_sessions: 3 });
  assert.equal(report.scopes.all.clients.codex.successful, 1);
  assert.equal(report.scopes.all.clients.claude.successful, 2);
  assert.equal(report.scopes.project.combined.attempts, 2);
  assert.equal(report.scopes.project.combined.matched_sessions, 2);
  assert.deepEqual(report.window, { days: 30, start: '2026-08-05T12:00:00Z', end: '2026-09-04T12:00:00Z' });
  const oldCodex = process.env.CODEX_HOME, oldClaude = process.env.CLAUDE_CONFIG_DIR;
  t.after(() => {
    if (oldCodex === undefined) delete process.env.CODEX_HOME; else process.env.CODEX_HOME = oldCodex;
    if (oldClaude === undefined) delete process.env.CLAUDE_CONFIG_DIR; else process.env.CLAUDE_CONFIG_DIR = oldClaude;
  });
  process.env.CLAUDE_CONFIG_DIR = options.claude_home;
  process.env.CODEX_HOME = options.codex_home;
  const skillReport = await analyze({ ...options, target_kind: 'skill', target_name: 'plugin-a:review', codex_home: undefined, claude_home: undefined, project: null });
  assert.equal(skillReport.scopes.all.combined.attempts, 3);
});

test('reports direct failures and coverage gaps without transcript text', async t => {
  const options = setup(t), skill = skillPath(options.root);
  const calls = [
    ['failure', `cat '${skill}'`, 'No such file: PRIVATE_TRANSCRIPT_TEXT'],
    ['diagnostic', `sed -n '1,20p' '/plugins/read-the-room/skills/write/SKILL.md'; wc -l '${skill}'`, 'An old transcript contained an error'],
    ['continuation', `sed -n '180,280p' '${skill}'`, 'Describe how failed commands are reported.'],
    ['multi', `cat '${skill}' '/plugins/other/skills/check/SKILL.md'`, `cat: ${skill}: No such file`],
  ];
  write(`${options.codex_home}/sessions/failure.jsonl`, [codex({ cwd: options.project }, 'session_meta'), ...calls.flatMap(([id, input, output]) => [codex({ type: 'custom_tool_call', name: 'exec', call_id: id, input }), codex({ type: 'custom_tool_call_output', call_id: id, output })])]);
  write(`${options.claude_home}/projects/sample/failure.jsonl`, [
    { type: 'future_record', timestamp: '2026-09-02T10:59:59Z', cwd: options.project },
    claude([skillCall('failure'), skillCall('incomplete')]),
    claude([{ type: 'tool_result', tool_use_id: 'failure', content: 'PRIVATE_TRANSCRIPT_TEXT', is_error: true }], { type: 'user' }),
    claude('Example: <command-name>plugin-a:review</command-name>'),
    claude([{ type: 'tool_result', tool_use_id: 'transcript-read', content: '<command-name>plugin-a:review</command-name>' }], { type: 'user', isMeta: true }),
  ], '{malformed\n');
  write(`${options.claude_home}/projects/unknown/session.jsonl`, [claude('<command-name>plugin-a:review</command-name>', { type: 'user', isMeta: true })]);
  const report = await analyze({ ...options, project: null, target_kind: 'skill', target_name: 'plugin-a:review' });
  assert.deepEqual(report.scopes.all.combined, { attempts: 5, successful: 1, problems: 3, incomplete: 1, scanned_sessions: 3, matched_sessions: 3 });
  assert.deepEqual(report.scopes.all.problem_categories, [{ client: 'claude', category: 'skill-error', count: 1 }, { client: 'codex', category: 'skill-load-error', count: 2 }]);
  assert.deepEqual(report.warnings, ['malformed-json', 'missing-session-cwd', 'unknown-record'].map(category => ({ client: 'claude', category, count: 1 })));
  assert.ok(!JSON.stringify(report).includes('PRIVATE_TRANSCRIPT_TEXT'));
  const missing = await analyze({ ...options, claude_home: `${options.root}/missing-claude` });
  assert.ok(missing.warnings.some(warning => warning.client === 'claude' && warning.category === 'missing-session-root' && warning.count === 1));
});

test('CLI validates flags and returns JSON with environment roots', t => {
  const options = setup(t);
  const script = path.resolve(__dirname, '../skills/inspect-plugin-usage/scripts/inspect_sessions.js');
  const run = args => spawnSync(process.execPath, [script, ...args], { cwd: options.root, env: { ...process.env, CODEX_HOME: options.codex_home, CLAUDE_CONFIG_DIR: options.claude_home }, encoding: 'utf8' });
  for (const args of [[], ['--plugin', 'a', '--skill', 'b'], ['--plugin', 'a', '--days', '0'], ['--plugin', 'a', '--days', '1.5'], ['--wat']]) assert.equal(run(args).status, 2);
  assert.equal(run(['--help']).status, 0);
  const result = run(['--plugin', 'plugin-a', '--days', '2', '--project', options.project]);
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.window.days, 2);
  assert.equal(report.scopes.all.combined.attempts, 0);
  assert.equal(report.warnings.length, 2);
});
