#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const shared = ['skills', 'scripts/render-deck.js', 'scripts/render-page.js', 'src', 'vendor', 'README.md', 'LICENSE', 'CHANGELOG.md', 'packaging/compatibility.md'];

function copy(source, destination) {
  const stat = fs.lstatSync(source);
  assert(!stat.isSymbolicLink(), `Package symlink rejected: ${source}`);
  if (stat.isDirectory()) {
    fs.mkdirSync(destination, {recursive:true});
    for (const name of fs.readdirSync(source)) copy(path.join(source, name), path.join(destination, name));
  } else {
    assert(stat.isFile(), 'Package entries must be ordinary files');
    fs.mkdirSync(path.dirname(destination), {recursive:true});
    fs.copyFileSync(source, destination, fs.constants.COPYFILE_EXCL);
  }
}

function packagePlugin(destination) {
  const parent = fs.realpathSync(path.dirname(path.resolve(destination)));
  const out = path.join(parent, path.basename(destination));
  assert(out !== root && !out.startsWith(root + path.sep), 'Release directory must be outside plugin');
  fs.mkdirSync(out);
  for (const target of ['portable', 'codex', 'claude']) {
    const folder = path.join(out, `copywriter-${target}`, 'copywriter');
    fs.mkdirSync(folder, {recursive:true});
    for (const item of shared) copy(path.join(root, item), path.join(folder, item));
    const manifest = target === 'portable' ? 'plugin.json' : `.${target}-plugin/plugin.json`;
    copy(path.join(root, manifest), path.join(folder, manifest));
  }
  return out;
}
if (require.main === module) {
  try { assert.equal(process.argv.length, 3, 'Usage: node scripts/package.js NEW_RELEASE_DIR'); console.log(packagePlugin(process.argv[2])); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = {packagePlugin};
