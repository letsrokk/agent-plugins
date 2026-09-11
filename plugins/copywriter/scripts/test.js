#!/usr/bin/env node
'use strict';
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const tests = fs.readdirSync(path.join(root, 'tests')).filter(file => file.endsWith('.test.js')).sort().map(file => path.join('tests', file));
if (!tests.length) throw new Error('No tests found');
const result = spawnSync(process.execPath, ['--test', ...tests], {cwd:root, stdio:'inherit'});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
