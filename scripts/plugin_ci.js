#!/usr/bin/env node
'use strict';

const { readdirSync, statSync } = require('node:fs');
const { resolve, join } = require('node:path');
const { execFileSync } = require('node:child_process');

const SHARED_CONTRACT_PATHS = new Set([
  '.github/workflows/validate.yml',
  'AGENTS.md',
  'docs/plugin-development.md',
  'scripts/plugin_ci.js',
  'scripts/validate_marketplaces.js',
  'package.json',
  'package-lock.json',
]);

function isDirectory(path) {
  return statSync(path, { throwIfNoEntry: false })?.isDirectory() ?? false;
}

function isScriptedPlugin(plugin) {
  if (isDirectory(join(plugin, 'scripts')) || isDirectory(join(plugin, 'src'))) return true;
  const skills = join(plugin, 'skills');
  return isDirectory(skills) && readdirSync(skills).some(name => isDirectory(join(skills, name, 'scripts')));
}

function allScriptedPlugins(root) {
  const plugins = join(root, 'plugins');
  return isDirectory(plugins) ? readdirSync(plugins).filter(name => isScriptedPlugin(join(plugins, name))).sort() : [];
}

function changedScriptedPlugins(root, base, head) {
  const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
  const mergeBase = git('merge-base', base, head).trim();
  const changed = git('diff', '--name-only', '-z', mergeBase, head).split('\0').filter(Boolean);
  if (changed.some(path => SHARED_CONTRACT_PATHS.has(path))) return allScriptedPlugins(root);
  const names = new Set(changed.map(path => path.split('/')).filter(parts => parts.length >= 3 && parts[0] === 'plugins').map(parts => parts[1]));
  return [...names].filter(name => isScriptedPlugin(join(root, 'plugins', name))).sort();
}

module.exports = { isScriptedPlugin, allScriptedPlugins, changedScriptedPlugins };

if (require.main === module) {
  const [command, base, head, ...extra] = process.argv.slice(2);
  if (command !== 'changed' || !base || !head || extra.length) {
    console.error('Usage: node scripts/plugin_ci.js changed BASE HEAD');
    process.exitCode = 2;
  } else {
    try {
      console.log(JSON.stringify(changedScriptedPlugins(resolve(__dirname, '..'), base, head)));
    } catch (error) {
      console.error(error.message);
      process.exitCode = 1;
    }
  }
}
