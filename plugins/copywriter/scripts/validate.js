#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const Ajv = require('ajv/dist/2020');
const root = path.resolve(__dirname, '..');
const json = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const manifest = json('plugin.json');
const validate = new Ajv().compile(json('packaging/plugin.schema.json'));
assert(validate(manifest), JSON.stringify(validate.errors));
for (const host of ['codex', 'claude']) {
  const native = json(`.${host}-plugin/plugin.json`);
  assert.equal(native.name, manifest.name);
  assert.equal(native.version, manifest.version);
  assert(!native.$schema);
  if (host === 'codex') assert.equal(native.skills, './skills/');
}
function walk(directory) {
  return fs.readdirSync(directory, {withFileTypes:true}).flatMap(entry => {
    if (entry.name === 'node_modules') return [];
    assert(!entry.isSymbolicLink(), 'No package symlinks');
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(file) : [file];
  });
}
const files = walk(root);
for (const file of files) {
  if (/\.(js|mjs)$/.test(file)) {
    const result = spawnSync(process.execPath, ['--check', file], {stdio:'inherit'});
    assert.equal(result.status, 0, `Syntax: ${file}`);
  }
  if (file.endsWith('.json')) JSON.parse(fs.readFileSync(file, 'utf8'));
  if (file.endsWith('SKILL.md')) {
    const source = fs.readFileSync(file, 'utf8');
    assert(Buffer.byteLength(source) <= 7168, 'Skill byte limit exceeded');
    const front = /^---\nname: ([a-z-]+)\ndescription: (.+)\n---/m.exec(source);
    assert(front && front[1] === path.basename(path.dirname(file)), `Skill frontmatter: ${file}`);
    assert(front[2].length <= 1024);
  }
  if (file.endsWith('.md') && file.includes(`${path.sep}skills${path.sep}`)) {
    const source = fs.readFileSync(file, 'utf8');
    for (const match of source.matchAll(/\[[^\]]*\]\(([^\s)]+)\)/g)) {
      const ref = match[1].split('#')[0];
      if (!ref || /^[a-z]+:/i.test(ref)) continue;
      const target = path.resolve(path.dirname(file), ref);
      assert(target.startsWith(root + path.sep), `Reference escapes plugin: ${ref}`);
      assert(fs.existsSync(target), `Missing reference in ${file}: ${ref}`);
    }
  }
}
assert.deepEqual(fs.readdirSync(path.join(root, 'skills')).sort(), ['article','landing-page','pitch-deck','readme','tagline','write']);
const build = spawnSync(process.execPath, ['scripts/build.js', '--check'], {cwd:root, stdio:'inherit'});
assert.equal(build.status, 0, 'Committed renderer bundle differs from locked build');
console.log('Copywriter manifests, skills, references, JSON and JavaScript validated.');
