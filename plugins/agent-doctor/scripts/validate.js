#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
for (const directory of ['scripts', 'skills', 'tests']) {
  for (const file of fs.readdirSync(path.join(root, directory), { recursive: true })) {
    if (!file.endsWith('.js')) continue;
    const result = spawnSync(process.execPath, ['--check', path.join(root, directory, file)], { stdio: 'inherit' });
    if (result.status !== 0) process.exitCode = 1;
  }
}
