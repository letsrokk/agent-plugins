'use strict';

const assert = require('node:assert/strict');
const { test } = require('node:test');
const { mkdtempSync, mkdirSync, writeFileSync, rmSync } = require('node:fs');
const { join, dirname } = require('node:path');
const { tmpdir } = require('node:os');
const { execFileSync } = require('node:child_process');
const { changedScriptedPlugins } = require('../scripts/plugin_ci.js');

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'plugin-ci-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
  git('init', '-b', 'main');
  git('config', 'user.name', 'Test User');
  git('config', 'user.email', 'test@example.com');
  const write = (path, content = 'test\n') => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), content);
  };
  const commit = message => {
    git('add', '-A');
    git('commit', '-m', message);
    return git('rev-parse', 'HEAD');
  };
  return { root, write, commit };
}

test('selects only changed scripted plugins present at head', t => {
  const { root, write, commit } = fixture(t);
  write('plugins/alpha/src/alpha.js');
  write('plugins/skill-only/skills/example/SKILL.md');
  write('plugins/deleted/scripts/helper.js');
  const base = commit('add plugins');
  write('plugins/alpha/src/alpha.js', 'changed\n');
  write('plugins/skill-only/skills/example/SKILL.md', 'changed\n');
  rmSync(join(root, 'plugins/deleted'), { recursive: true });
  write('plugins/new-scripted/skills/example/scripts/check.js');
  const head = commit('change plugins');
  assert.deepEqual(changedScriptedPlugins(root, base, head), ['alpha', 'new-scripted']);
});

test('shared contract and dependency changes select every scripted plugin', t => {
  const { root, write, commit } = fixture(t);
  write('plugins/alpha/src/alpha.js');
  write('plugins/gamma/skills/example/scripts/check.js');
  write('plugins/skill-only/skills/example/SKILL.md');
  let base = commit('add plugins');
  for (const path of ['docs/plugin-development.md', 'scripts/plugin_ci.js', 'scripts/validate_marketplaces.js', 'package.json', 'package-lock.json']) {
    write(path);
    const head = commit(`change ${path}`);
    assert.deepEqual(changedScriptedPlugins(root, base, head), ['alpha', 'gamma']);
    base = head;
  }
});
