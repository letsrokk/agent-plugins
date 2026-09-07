#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SEMVER = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/;

class Version {
  constructor(major, minor, patch) {
    this.major = BigInt(major);
    this.minor = BigInt(minor);
    this.patch = BigInt(patch);
  }

  static parse(value, filename, errors) {
    const match = typeof value === 'string' && SEMVER.exec(value);
    if (!match || match[0] !== value) {
      errors.push(`${filename}: version ${JSON.stringify(value)} must use stable MAJOR.MINOR.PATCH SemVer`);
      return null;
    }
    return new Version(...match.slice(1));
  }

  compare(other) {
    for (const part of ['major', 'minor', 'patch']) {
      if (this[part] < other[part]) return -1;
      if (this[part] > other[part]) return 1;
    }
    return 0;
  }

  bumpPatch() {
    return new Version(this.major, this.minor, this.patch + 1n);
  }

  toString() {
    return `${this.major}.${this.minor}.${this.patch}`;
  }
}

class VersioningError extends Error {
  constructor(errors) {
    super(errors.join('\n'));
    this.errors = errors;
  }
}

function git(root, ...args) {
  const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
  if (result.error) throw result.error;
  return result;
}

function readRevisionFile(root, revision, filename) {
  const result = git(root, 'show', `${revision}:${filename}`);
  return result.status === 0 ? result.stdout : null;
}

function readWorktreeFile(root, filename) {
  try {
    return fs.readFileSync(path.join(root, filename), 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}

function jsonVersion(text, filename, errors) {
  let payload;
  try {
    payload = JSON.parse(text);
  } catch (error) {
    errors.push(`${filename}: invalid JSON: ${error.message}`);
    return [null, null];
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    errors.push(`${filename}: root value must be an object`);
    return [null, null];
  }
  return [payload.version, Version.parse(payload.version, filename, errors)];
}

function manifestPaths(name) {
  return ['plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json']
    .map(filename => `plugins/${name}/${filename}`);
}

function validateSurfaces(readFile, name, errors) {
  const [portablePath, ...compatibilityPaths] = manifestPaths(name);
  const portableText = readFile(portablePath);
  if (portableText === null) return null;
  const [portableValue, portableVersion] = jsonVersion(portableText, portablePath, errors);
  for (const filename of compatibilityPaths) {
    const text = readFile(filename);
    if (text === null) continue;
    const [value] = jsonVersion(text, filename, errors);
    if (value !== portableValue) {
      errors.push(`${filename}: version ${JSON.stringify(value)} must match portable manifest version ${portableValue}`);
    }
  }
  return portableVersion;
}

function analyzeChanges(root, base, head) {
  const errors = [];
  for (const revision of [base, head]) {
    if (git(root, 'rev-parse', '--verify', '--end-of-options', `${revision}^{commit}`).status !== 0) {
      errors.push(`invalid Git revision ${JSON.stringify(revision)}`);
    }
  }
  if (errors.length) throw new VersioningError(errors);
  const result = git(root, 'diff', '--name-only', '-z', base, head, '--', 'plugins/');
  if (result.status !== 0) throw new VersioningError([result.stderr.trim() || 'git diff failed']);
  const names = [...new Set(result.stdout.split('\0')
    .map(filename => filename.split('/'))
    .filter(parts => parts.length >= 3 && parts[0] === 'plugins')
    .map(parts => parts[1]))].sort();
  const changes = [];
  for (const name of names) {
    const portablePath = manifestPaths(name)[0];
    if (readRevisionFile(root, head, portablePath) === null) continue;
    const headVersion = validateSurfaces(filename => readRevisionFile(root, head, filename), name, errors);
    const baseText = readRevisionFile(root, base, portablePath);
    if (baseText === null) continue;
    const baseErrors = [];
    const [, baseVersion] = jsonVersion(baseText, portablePath, baseErrors);
    errors.push(...baseErrors.map(error => `${error} at ${base}`));
    if (!baseVersion || !headVersion) continue;
    if (headVersion.compare(baseVersion) < 0) {
      errors.push(`plugins/${name}: version decreased from ${baseVersion} to ${headVersion}`);
      continue;
    }
    changes.push({ name, baseVersion, headVersion });
  }
  if (errors.length) throw new VersioningError(errors);
  return changes;
}

function applyChanges(root, changes) {
  const errors = [];
  const currentVersions = new Map(changes.map(change => [change.name,
    validateSurfaces(filename => readWorktreeFile(root, filename), change.name, errors)]));
  if (errors.length) throw new VersioningError(errors);
  const updates = [];
  for (const change of changes) {
    const current = currentVersions.get(change.name);
    if (!current || current.compare(change.headVersion) > 0) continue;
    if (current.compare(change.headVersion) < 0) {
      errors.push(`plugins/${change.name}: current version ${current} is older than event version ${change.headVersion}; refusing to restore stale event version ${change.headVersion}`);
      continue;
    }
    if (change.headVersion.compare(change.baseVersion) > 0) continue;
    updates.push([change.name, current.bumpPatch()]);
  }
  if (errors.length) throw new VersioningError(errors);
  for (const [name, version] of updates) {
    for (const filename of manifestPaths(name)) {
      const text = readWorktreeFile(root, filename);
      if (text === null) continue;
      const payload = JSON.parse(text);
      payload.version = String(version);
      fs.writeFileSync(path.join(root, filename), `${JSON.stringify(payload, null, 2)}\n`);
    }
  }
  return updates;
}

function main(args = process.argv.slice(2)) {
  if (args.length !== 3 || !['check', 'apply'].includes(args[0])) {
    console.error('Usage: node scripts/version_plugins.js <check|apply> BASE HEAD');
    return 2;
  }
  const [command, base, head] = args;
  try {
    const changes = analyzeChanges(process.cwd(), base, head);
    if (command === 'check') {
      console.log(`Plugin version policy passed for ${changes.length} changed plugin(s).`);
      return 0;
    }
    const updates = applyChanges(process.cwd(), changes);
    if (!updates.length) console.log('No plugin version changes required.');
    for (const [name, version] of updates) console.log(`${name}: ${version}`);
    return 0;
  } catch (error) {
    if (!(error instanceof VersioningError)) throw error;
    for (const message of error.errors) console.error(message);
    return 1;
  }
}

module.exports = { Version, VersioningError, analyzeChanges, applyChanges };
if (require.main === module) process.exitCode = main();
