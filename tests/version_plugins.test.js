'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');
const { Version } = require('../scripts/version_plugins.js');

const VERSION_SCRIPT = path.resolve(__dirname, '../scripts/version_plugins.js');

function repository(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'plugin-versioning-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  function git(...args) {
    const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  }
  function write(filename, text) {
    fs.mkdirSync(path.dirname(path.join(root, filename)), { recursive: true });
    fs.writeFileSync(path.join(root, filename), text);
  }
  function writeJson(filename, payload) {
    write(filename, `${JSON.stringify(payload, null, 2)}\n`);
  }
  function plugin(name, version, { codex = true, claude = false } = {}) {
    writeJson(`plugins/${name}/plugin.json`, { name, version });
    if (codex) writeJson(`plugins/${name}/.codex-plugin/plugin.json`, { name, version });
    if (claude) writeJson(`plugins/${name}/.claude-plugin/plugin.json`, { name, version });
  }
  function commit(message) {
    git('add', '-A');
    git('commit', '-m', message);
    return git('rev-parse', 'HEAD');
  }
  function run(...args) {
    return spawnSync(process.execPath, [VERSION_SCRIPT, ...args], { cwd: root, encoding: 'utf8' });
  }
  function version(filename) {
    return JSON.parse(fs.readFileSync(path.join(root, filename), 'utf8')).version;
  }
  git('init', '-b', 'main');
  git('config', 'user.name', 'Test User');
  git('config', 'user.email', 'test@example.com');
  return { root, git, write, writeJson, plugin, commit, run, version };
}

function success(result) {
  assert.equal(result.status, 0, result.stderr);
}

test('apply patch bumps all changed plugins and synchronizes manifests; bot commits are idempotent', t => {
  const r = repository(t);
  r.plugin('alpha-plugin', '1.2.3', { claude: true });
  r.plugin('beta', '0.9.9');
  r.writeJson('plugins/alpha-plugin/package.json', { name: 'alpha-plugin', private: true });
  const base = r.commit('add plugins');
  r.write('plugins/alpha-plugin/README.md', 'changed\n');
  r.write('plugins/beta/README.md', 'changed\n');
  const head = r.commit('change plugins');
  success(r.run('apply', base, head));
  for (const filename of ['plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json']) {
    assert.equal(r.version(`plugins/alpha-plugin/${filename}`), '1.2.4');
  }
  assert.equal(r.version('plugins/alpha-plugin/package.json'), undefined);
  assert.equal(r.version('plugins/beta/plugin.json'), '0.9.10');
  const botHead = r.commit('chore: bump plugin versions');
  success(r.run('apply', head, botHead));
  assert.equal(r.git('status', '--porcelain'), '');
});

test('explicit version is preserved and new or deleted plugins are excluded', t => {
  const r = repository(t);
  r.plugin('existing', '1.2.3', { claude: true });
  r.plugin('deleted', '0.1.0');
  const base = r.commit('add existing plugins');
  r.plugin('existing', '2.0.0', { claude: true });
  r.write('plugins/existing/README.md', 'changed\n');
  fs.rmSync(path.join(r.root, 'plugins/deleted'), { recursive: true });
  r.plugin('new-plugin', '0.1.0');
  r.write('README.md', 'repository docs\n');
  const head = r.commit('make mixed changes');
  const check = r.run('check', base, head);
  success(check);
  assert.match(check.stdout, /passed for 1 changed plugin/);
  success(r.run('apply', base, head));
  assert.equal(r.version('plugins/existing/plugin.json'), '2.0.0');
  assert.equal(r.version('plugins/new-plugin/plugin.json'), '0.1.0');
  assert.equal(r.git('status', '--porcelain'), '');
});

test('newer main version covers an older unversioned change', t => {
  const r = repository(t);
  r.plugin('example', '1.2.3', { claude: true });
  const base = r.commit('add plugin');
  r.write('plugins/example/README.md', 'first change\n');
  const head = r.commit('change plugin without version');
  r.plugin('example', '2.0.0', { claude: true });
  r.commit('publish later version');
  success(r.run('apply', base, head));
  assert.equal(r.version('plugins/example/plugin.json'), '2.0.0');
  assert.equal(r.git('status', '--porcelain'), '');
});

test('stale explicit event does not restore its version or partially bump other plugins', t => {
  const r = repository(t);
  r.plugin('example', '1.2.3');
  r.plugin('alpha', '0.1.0');
  const base = r.commit('add plugins');
  r.plugin('example', '2.0.0');
  r.write('plugins/alpha/README.md', 'changed\n');
  const head = r.commit('request major version');
  r.plugin('example', '1.5.0');
  r.commit('replace event version on main');
  const result = r.run('apply', base, head);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /refusing to restore stale event version 2\.0\.0/);
  assert.equal(r.version('plugins/example/plugin.json'), '1.5.0');
  assert.equal(r.version('plugins/alpha/plugin.json'), '0.1.0');
  assert.equal(r.git('status', '--porcelain'), '');
});

test('plugin deleted after event is a no-op', t => {
  const r = repository(t);
  r.plugin('example', '1.2.3');
  const base = r.commit('add plugin');
  r.write('plugins/example/README.md', 'changed\n');
  const head = r.commit('change plugin');
  fs.rmSync(path.join(r.root, 'plugins/example'), { recursive: true });
  r.commit('delete plugin');
  success(r.run('apply', base, head));
  assert.equal(fs.existsSync(path.join(r.root, 'plugins/example')), false);
  assert.equal(r.git('status', '--porcelain'), '');
});

test('check rejects decreased version', t => {
  const r = repository(t);
  r.plugin('example', '1.2.3');
  const base = r.commit('add plugin');
  r.plugin('example', '1.2.2');
  const head = r.commit('decrease version');
  const result = r.run('check', base, head);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /version decreased from 1\.2\.3 to 1\.2\.2/);
});

test('check rejects invalid and inconsistent versions', t => {
  const r = repository(t);
  r.plugin('example', '1.2.3', { claude: true });
  const base = r.commit('add plugin');
  r.plugin('example', '2.0.0', { claude: true });
  r.writeJson('plugins/example/.claude-plugin/plugin.json', { name: 'example', version: 'v2' });
  const head = r.commit('write invalid compatibility version');
  const result = r.run('check', base, head);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must use stable MAJOR.MINOR.PATCH SemVer/);
  assert.match(result.stderr, /must match portable manifest version 2\.0\.0/);
});

test('check validates new plugin version without scheduling a bump', t => {
  const r = repository(t);
  r.write('README.md', 'repository\n');
  const base = r.commit('initialize repository');
  r.plugin('new-plugin', '0.1');
  const head = r.commit('add plugin with invalid release version');
  const result = r.run('check', base, head);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must use stable MAJOR.MINOR.PATCH SemVer/);
});

test('stable SemVer rejects suffixes and leading zeros and preserves arbitrary precision', () => {
  for (const value of ['01.2.3', '1.02.3', '1.2.03', '1.2.3-rc.1', '1.2.3+build', '1.2.3\n', 123, null]) {
    const errors = [];
    assert.equal(Version.parse(value, 'plugin.json', errors), null);
    assert.equal(errors.length, 1);
  }
  const errors = [];
  const version = Version.parse('9007199254740993.0.9007199254740993', 'plugin.json', errors);
  assert.equal(String(version.bumpPatch()), '9007199254740993.0.9007199254740994');
  assert.equal(version.compare(Version.parse('9007199254740992.999.999', 'plugin.json', errors)), 1);
  assert.deepEqual(errors, []);
});

test('CLI rejects invalid revisions and arguments', t => {
  const r = repository(t);
  r.write('README.md', 'repository\n');
  const head = r.commit('initialize repository');
  const result = r.run('check', 'missing-revision', head);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /invalid Git revision/);
  assert.equal(r.run('apply', head).status, 2);
});
