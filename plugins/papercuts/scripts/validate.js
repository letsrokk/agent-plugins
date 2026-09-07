#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root = fileURLToPath(new URL('../',import.meta.url));
for (const directory of ['src','scripts','tests','dist']) {
  for (const file of fs.readdirSync(path.join(root,directory),{recursive:true}).filter(name => name.endsWith('.js') || name === 'papercuts')) {
    const result = spawnSync(process.execPath,['--check',path.join(root,directory,file)],{stdio:'inherit'});
    if (result.status !== 0 || result.error) process.exit(1);
  }
}
const hook = JSON.parse(fs.readFileSync(path.join(root,'hooks/hooks.json'),'utf8')).hooks.SessionStart[0].hooks[0];
assert.equal(hook.statusMessage,'Loading Papercuts instructions...');
assert.equal(hook.command,'node "${CLAUDE_PLUGIN_ROOT}/scripts/session_start.js"');
for (const name of ['.codex-plugin','.claude-plugin']) {
  const manifest = JSON.parse(fs.readFileSync(path.join(root,name,'plugin.json'),'utf8'));
  assert.equal(manifest.mcpServers.papercuts.command,'node');
  assert.equal(manifest.version,JSON.parse(fs.readFileSync(path.join(root,'plugin.json'),'utf8')).version);
}
const result = spawnSync(process.execPath,['scripts/build.js','--check'],{cwd:root,stdio:'inherit'});
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
