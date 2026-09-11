#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const { buildSync } = require('esbuild');
const root = path.resolve(__dirname, '..');
const target = path.join(root, 'vendor/deck.cjs');
const result = buildSync({ absWorkingDir: root, entryPoints: ['src/deck.js'], bundle: true, platform: 'node', target: 'node24', outfile: target, write: false });
const content = result.outputFiles[0].contents;
if (process.argv.includes('--check')) {
  if (!fs.readFileSync(target).equals(Buffer.from(content))) throw new Error('Deck bundle is stale; run npm run build');
} else fs.writeFileSync(target, content);
