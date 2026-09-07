#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const root = path.resolve(__dirname, '..');
const tests = fs.readdirSync(path.join(root, 'tests')).filter(file => file.endsWith('.test.js')).sort().map(file => path.join('tests', file));
const result = spawnSync(process.execPath, ['--test', ...tests], { cwd: root, stdio: 'inherit' });
process.exitCode = result.status ?? 1;
