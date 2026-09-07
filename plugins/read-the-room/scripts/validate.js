#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const { readFileSync, readdirSync, statSync } = require('node:fs');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');

try {
  const root = resolve(__dirname, '..');
  for (const directory of ['scripts', 'tests']) {
    for (const file of readdirSync(resolve(root, directory)).filter((name) => name.endsWith('.js'))) {
      const result = spawnSync(process.execPath, ['--check', resolve(root, directory, file)], { stdio: 'inherit' });
      if (result.status !== 0) throw new Error(`Invalid JavaScript: ${directory}/${file}`);
    }
  }
  const config = JSON.parse(readFileSync(resolve(root, 'hooks/hooks.json'), 'utf8'));
  assert.deepEqual(config, { hooks: { SessionStart: [{ hooks: [{
    type: 'command',
    command: 'node "${CLAUDE_PLUGIN_ROOT}/scripts/session_start.js"',
    timeout: 5,
    statusMessage: 'Loading Read the Room writing guidance...',
  }] }] } });
  const skill = resolve(root, 'skills/make-it-make-sense');
  const policy = readFileSync(resolve(skill, 'SKILL.md'), 'utf8');
  for (const [, reference] of policy.matchAll(/\]\((references\/[^)]+)\)/g)) {
    assert.ok(statSync(resolve(skill, reference)).isFile(), `Missing channel reference: ${reference}`);
  }
  const result = spawnSync(process.execPath, [resolve(root, 'scripts/session_start.js')], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || 'SessionStart handler failed');
  assert.equal(JSON.parse(result.stdout).hookSpecificOutput.hookEventName, 'SessionStart');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
