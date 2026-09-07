#!/usr/bin/env node
'use strict';

const { spawnSync } = require('node:child_process');
const { resolve } = require('node:path');

const result = spawnSync(process.execPath, ['--test', resolve(__dirname, '../tests/session_start.test.js')], { stdio: 'inherit' });
if (result.error) console.error(result.error.message);
process.exitCode = result.status ?? 1;
