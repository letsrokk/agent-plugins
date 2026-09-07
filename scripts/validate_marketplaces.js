#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { parseArgs, isDeepStrictEqual } = require('node:util');
const { parse: parseToml } = require('smol-toml');
const { isScriptedPlugin } = require('./plugin_ci.js');

const CODEX_CATALOG = '.agents/plugins/marketplace.json';
const CLAUDE_CATALOG = '.claude-plugin/marketplace.json';
const AGENT_PLUGIN_SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json';
const CLAUDE_MARKETPLACE_SCHEMA = 'https://json.schemastore.org/claude-code-marketplace.json';
const MAX_SKILL_FILE_BYTES = 7168;
const PORTABLE_MANIFEST_FIELDS = new Set([
  '$schema', 'name', 'version', 'description', 'author', 'homepage', 'repository',
  'license', 'keywords', 'extensions',
]);
const AUTHOR_FIELDS = new Set(['name', 'email', 'url']);
const PR_REVIEW_TOOLKIT_AGENTS = [
  'pr_review_toolkit_code_reviewer', 'pr_review_toolkit_code_simplifier',
  'pr_review_toolkit_comment_analyzer', 'pr_review_toolkit_pr_test_analyzer',
  'pr_review_toolkit_silent_failure_hunter', 'pr_review_toolkit_type_design_analyzer',
];
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isFile = file => fs.statSync(file, { throwIfNoEntry: false })?.isFile() ?? false;
const isDirectory = file => fs.statSync(file, { throwIfNoEntry: false })?.isDirectory() ?? false;
const readText = file => new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(fs.readFileSync(file));
const directories = directory => fs.readdirSync(directory).sort()
  .map(name => path.join(directory, name)).filter(isDirectory);

function loadJson(root, relativePath, errors) {
  let payload;
  try {
    payload = JSON.parse(readText(path.join(root, relativePath)));
  } catch (error) {
    if (error.code === 'ENOENT') errors.push(`${relativePath}: file is missing`);
    else if (error instanceof SyntaxError) errors.push(`${relativePath}: invalid JSON: ${error.message}`);
    else throw error;
    return null;
  }
  if (!isObject(payload)) {
    errors.push(`${relativePath}: root value must be an object`);
    return null;
  }
  return payload;
}

function validateManifestMetadata(relativePath, manifest, errors) {
  for (const field of Object.keys(manifest).filter(field => !PORTABLE_MANIFEST_FIELDS.has(field)).sort()) {
    errors.push(`${relativePath}: unknown field '${field}'`);
  }
  for (const field of ['description', 'homepage', 'license', 'repository', 'version']) {
    if (Object.hasOwn(manifest, field) && typeof manifest[field] !== 'string') {
      errors.push(`${relativePath}: ${field} must be a string`);
    }
  }
  const { author, keywords, extensions } = manifest;
  if (author != null) {
    if (!isObject(author)) errors.push(`${relativePath}: author must be an object`);
    else {
      for (const field of Object.keys(author).filter(field => !AUTHOR_FIELDS.has(field)).sort()) {
        errors.push(`${relativePath}: author has unknown field '${field}'`);
      }
      for (const [field, value] of Object.entries(author)) {
        if (AUTHOR_FIELDS.has(field) && typeof value !== 'string') {
          errors.push(`${relativePath}: author.${field} must be a string`);
        }
      }
    }
  }
  if (keywords != null && (!Array.isArray(keywords) || keywords.some(value => typeof value !== 'string'))) {
    errors.push(`${relativePath}: keywords must be an array of strings`);
  }
  if (extensions != null && (!isObject(extensions) || Object.values(extensions).some(value => !isObject(value)))) {
    errors.push(`${relativePath}: extensions must map namespaces to objects`);
  }
}

function skillFrontmatterName(file, relativePath, errors) {
  let lines;
  try {
    lines = readText(file).split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/);
  } catch (error) {
    if (error.code !== 'ERR_ENCODING_INVALID_ENCODED_DATA') throw error;
    errors.push(`${relativePath}: must be UTF-8 text`);
    return null;
  }
  if (lines[0] !== '---') {
    errors.push(`${relativePath}: must start with YAML frontmatter`);
    return null;
  }
  const closing = lines.indexOf('---', 1);
  if (closing === -1) {
    errors.push(`${relativePath}: YAML frontmatter is not closed`);
    return null;
  }
  for (const line of lines.slice(1, closing)) {
    const match = /^name:\s*([^#]+?)\s*$/u.exec(line);
    if (match) return match[1].replace(/^['"]+|['"]+$/g, '');
  }
  errors.push(`${relativePath}: YAML frontmatter must define name`);
  return null;
}

function validateCustomAgents(root, skillDirectory, relativeSkill, errors) {
  const agents = path.join(skillDirectory, 'agents');
  if (!fs.existsSync(agents)) return;
  if (!isDirectory(agents)) {
    errors.push(`${relativeSkill}/agents: must be a directory`);
    return;
  }
  for (const filename of fs.readdirSync(agents).filter(name => name.endsWith('.toml')).sort()) {
    const agent = path.join(agents, filename);
    const relativeAgent = path.relative(root, agent);
    let payload;
    try {
      payload = parseToml(readText(agent));
    } catch (error) {
      errors.push(`${relativeAgent}: invalid TOML: ${error.message}`);
      continue;
    }
    const stem = path.basename(filename, '.toml');
    if (payload.name !== stem) errors.push(`${relativeAgent}: agent name must match filename '${stem}'`);
  }
}

function validatePluginComponents(root, name, errors) {
  const plugin = path.join(root, 'plugins', name);
  const skills = path.join(plugin, 'skills');
  let discoveredSkills = 0;
  if (fs.existsSync(skills)) {
    if (!isDirectory(skills)) errors.push(`plugins/${name}/skills: must be a directory`);
    else {
      for (const skillDirectory of directories(skills)) {
        const skillFile = path.join(skillDirectory, 'SKILL.md');
        if (!isFile(skillFile)) continue;
        discoveredSkills += 1;
        const relativeSkill = path.relative(root, skillDirectory);
        const relativeFile = path.relative(root, skillFile);
        const skillSize = fs.statSync(skillFile).size;
        if (skillSize > MAX_SKILL_FILE_BYTES) {
          errors.push(`${relativeFile}: must not exceed ${MAX_SKILL_FILE_BYTES} bytes (found ${skillSize})`);
        }
        const skillName = skillFrontmatterName(skillFile, relativeFile, errors);
        if (skillName !== null && skillName !== path.basename(skillDirectory)) {
          errors.push(`${relativeFile}: skill name must match directory '${path.basename(skillDirectory)}'`);
        }
        validateCustomAgents(root, skillDirectory, relativeSkill, errors);
      }
    }
  }
  if (discoveredSkills === 0 && !isFile(path.join(plugin, 'mcp.json'))) {
    errors.push(`plugins/${name}: must provide at least one skill or mcp.json`);
  }
}

function validateAdaptedPlugin(root, name, errors) {
  const title = name === 'code-simplifier' ? 'Code Simplifier' : 'PR Review Toolkit';
  const plugin = `plugins/${name}`;
  const skill = `${plugin}/skills/${name}`;
  const notice = path.join(root, plugin, 'NOTICE');
  if (!isFile(notice)) errors.push(`${plugin}/NOTICE is missing`);
  else {
    const text = readText(notice);
    for (const marker of ['Anthropic', 'Rokk Club', 'adapt',
      `https://github.com/anthropics/claude-plugins-official/tree/main/plugins/${name}`]) {
      if (!text.includes(marker)) errors.push(`${plugin}/NOTICE: missing attribution marker '${marker}'`);
    }
  }
  const license = path.join(root, plugin, 'LICENSE');
  if (isFile(license)) {
    const text = readText(license);
    if (!text.includes('Apache License') || !text.includes('Version 2.0')) {
      errors.push(`${plugin}/LICENSE: must contain Apache License 2.0`);
    }
  }
  const skillFile = path.join(root, skill, 'SKILL.md');
  if (isFile(skillFile)) {
    const text = readText(skillFile);
    if (!text.includes(`Anthropic's ${title}`) || (name === 'code-simplifier' && !text.includes('code_simplifier_agent'))) {
      errors.push(`${skill}/SKILL.md: adaptation notice is missing`);
    }
  }
  const interfaceFile = path.join(root, skill, 'agents/openai.yaml');
  const interfaceText = isFile(interfaceFile) ? readText(interfaceFile) : '';
  if (!new RegExp(`^\\s*display_name:\\s*['"]?${title}['"]?\\s*$`, 'm').test(interfaceText)) {
    errors.push(`${skill}/agents/openai.yaml: ${title} interface metadata is missing`);
  }
  const agents = name === 'code-simplifier' ? ['code_simplifier_agent'] : PR_REVIEW_TOOLKIT_AGENTS;
  for (const agentName of agents) {
    const agent = `${skill}/agents/${agentName}.toml`;
    if (!isFile(path.join(root, agent))) errors.push(`${agent} is missing`);
    else if (name === 'code-simplifier' && !readText(path.join(root, agent)).includes("Adapted from Anthropic's Code Simplifier")) {
      errors.push(`${agent}: adaptation notice is missing`);
    }
  }
}

function validatePortableManifest(root, name, catalog, errors) {
  const relativePath = `plugins/${name}/plugin.json`;
  const manifest = loadJson(root, relativePath, errors);
  if (manifest === null) {
    if (!fs.existsSync(path.join(root, relativePath))) {
      errors[errors.length - 1] = `${catalog}: plugin '${name}' is missing portable manifest ${relativePath}`;
    }
    return null;
  }
  const hasNativeManifest = ['.codex-plugin', '.claude-plugin']
    .some(client => isFile(path.join(root, 'plugins', name, client, 'plugin.json')));
  if (manifest.$schema !== AGENT_PLUGIN_SCHEMA && !(!Object.hasOwn(manifest, '$schema') && hasNativeManifest)) {
    errors.push(`${relativePath}: $schema must be ${AGENT_PLUGIN_SCHEMA}`);
  }
  if (manifest.name !== name) errors.push(`${relativePath}: name must match catalog entry '${name}'`);
  if (typeof manifest.version !== 'string' || !manifest.version) {
    errors.push(`${relativePath}: version must be a non-empty string`);
  }
  validateManifestMetadata(relativePath, manifest, errors);
  validatePluginComponents(root, name, errors);
  if (typeof manifest.license === 'string' && manifest.license !== 'MIT' && !isFile(path.join(root, 'plugins', name, 'LICENSE'))) {
    errors.push(`plugins/${name}: declares ${manifest.license} but has no package LICENSE`);
  }
  if (name === 'code-simplifier' || name === 'pr-review-toolkit') validateAdaptedPlugin(root, name, errors);
  return manifest;
}

function validateClientManifest(root, name, portableManifest, codex, errors) {
  const client = codex ? 'Codex' : 'Claude';
  const relativePath = `plugins/${name}/.${codex ? 'codex' : 'claude'}-plugin/plugin.json`;
  const manifest = loadJson(root, relativePath, errors);
  if (manifest === null) {
    if (!fs.existsSync(path.join(root, relativePath))) {
      errors[errors.length - 1] = `${codex ? CODEX_CATALOG : CLAUDE_CATALOG}: plugin '${name}' is missing ${client} compatibility manifest ${relativePath}`;
    }
    return;
  }
  if (manifest.name !== name) errors.push(`${relativePath}: name must match catalog entry '${name}'`);
  if (!codex) return;
  const nativeComponents = Object.hasOwn(manifest, 'hooks') || Object.hasOwn(manifest, 'mcpServers')
    || isFile(path.join(root, 'plugins', name, 'hooks/hooks.json'));
  if (portableManifest.$schema === AGENT_PLUGIN_SCHEMA && nativeComponents) {
    errors.push(`plugins/${name}/plugin.json: omit $schema to enable native Codex hooks or mcpServers`);
  }
  if (typeof portableManifest.version === 'string' && portableManifest.version && manifest.version !== portableManifest.version) {
    errors.push(`${relativePath}: version must match portable manifest '${portableManifest.version}'`);
  }
  const skills = path.join(root, 'plugins', name, 'skills');
  const hasSkill = isDirectory(skills) && directories(skills).some(child => isFile(path.join(child, 'SKILL.md')));
  if (hasSkill) {
    if (manifest.skills !== './skills/') errors.push(`${relativePath}: skills must be './skills/'`);
  } else if (Object.hasOwn(manifest, 'skills')) {
    errors.push(`${relativePath}: skills must be omitted when no skills are present`);
  }
}

function validatePlugins(root, catalogPath, plugins, codex, errors) {
  if (!Array.isArray(plugins)) {
    errors.push(`${catalogPath}: plugins must be an array`);
    return;
  }
  const seen = new Set();
  for (const [index, entry] of plugins.entries()) {
    const prefix = `${catalogPath}: plugins[${index}]`;
    if (!isObject(entry)) {
      errors.push(`${prefix} must be an object`);
      continue;
    }
    const { name } = entry;
    if (typeof name !== 'string' || !/^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$/u.test(name)
      || /[\r\n\u2028\u2029]/.test(name) || name.includes('--') || name.includes('..')) {
      errors.push(`${prefix}.name is not a valid Agent Plugins name`);
      continue;
    }
    if (seen.has(name)) errors.push(`${catalogPath}: duplicate plugin name '${name}'`);
    seen.add(name);
    if (codex) {
      if (!isObject(entry.policy) || entry.policy.installation !== 'AVAILABLE') {
        errors.push(`${prefix}.policy.installation must be 'AVAILABLE'`);
      }
      if (!isObject(entry.policy) || entry.policy.authentication !== 'ON_INSTALL') {
        errors.push(`${prefix}.policy.authentication must be 'ON_INSTALL'`);
      }
      if (typeof entry.category !== 'string' || !entry.category.trim()) {
        errors.push(`${prefix}.category must be a non-empty string`);
      }
    }
    const source = codex ? (isObject(entry.source) && entry.source.source === 'local' ? entry.source.path : null) : entry.source;
    if (source !== `./plugins/${name}`) {
      errors.push(`${prefix}.source must be './plugins/${name}'`);
      continue;
    }
    if (!isDirectory(path.join(root, 'plugins', name))) {
      errors.push(`${catalogPath}: plugin '${name}' directory is missing`);
      continue;
    }
    const portableManifest = validatePortableManifest(root, name, catalogPath, errors);
    if (!codex || portableManifest !== null) validateClientManifest(root, name, portableManifest, codex, errors);
  }
}

function validateRepository(root) {
  root = path.resolve(root);
  const errors = [];
  const codex = loadJson(root, CODEX_CATALOG, errors);
  if (codex !== null) {
    if (codex.name !== 'rokk-club-codex-plugins') errors.push(`${CODEX_CATALOG}: name must be 'rokk-club-codex-plugins'`);
    if (!isDeepStrictEqual(codex.interface, { displayName: 'Rokk Club Codex Plugins' })) {
      errors.push(`${CODEX_CATALOG}: interface.displayName must be 'Rokk Club Codex Plugins'`);
    }
    validatePlugins(root, CODEX_CATALOG, codex.plugins, true, errors);
  }
  const claude = loadJson(root, CLAUDE_CATALOG, errors);
  if (claude !== null) {
    if (claude.$schema !== CLAUDE_MARKETPLACE_SCHEMA) errors.push(`${CLAUDE_CATALOG}: $schema must be ${CLAUDE_MARKETPLACE_SCHEMA}`);
    if (claude.name !== 'rokk-club-claude-plugins') errors.push(`${CLAUDE_CATALOG}: name must be 'rokk-club-claude-plugins'`);
    if (!isDeepStrictEqual(claude.owner, { name: 'Rokk Club' })) errors.push(`${CLAUDE_CATALOG}: owner.name must be 'Rokk Club'`);
    validatePlugins(root, CLAUDE_CATALOG, claude.plugins, false, errors);
  }
  if (!isFile(path.join(root, 'AGENTS.md'))) errors.push('AGENTS.md is missing');
  const instructions = path.join(root, 'CLAUDE.md');
  if (!fs.lstatSync(instructions, { throwIfNoEntry: false })?.isSymbolicLink() || fs.readlinkSync(instructions) !== 'AGENTS.md') {
    errors.push('CLAUDE.md must be a symlink to AGENTS.md');
  }
  const plugins = path.join(root, 'plugins');
  if (isDirectory(plugins)) {
    for (const plugin of directories(plugins)) {
      if (!isScriptedPlugin(plugin)) continue;
      for (const entrypoint of ['test.js', 'validate.js']) {
        if (!isFile(path.join(plugin, 'scripts', entrypoint))) {
          errors.push(`plugins/${path.basename(plugin)}/scripts/${entrypoint} is missing`);
        }
      }
    }
  }
  return errors;
}

function main() {
  const { values, positionals } = parseArgs({ options: { help: { type: 'boolean', short: 'h' } }, allowPositionals: true });
  if (values.help) {
    console.log('Usage: node scripts/validate_marketplaces.js [repository]\nValidate the Rokk Club marketplace catalogs and referenced plugins.');
    return;
  }
  if (positionals.length > 1) throw new Error('Expected at most one repository root');
  const errors = validateRepository(positionals[0] ?? path.resolve(__dirname, '..'));
  if (errors.length) {
    for (const error of errors) console.error(`error: ${error}`);
    process.exitCode = 1;
  } else console.log('Marketplace validation passed.');
}

module.exports = { validateRepository };
if (require.main === module) main();
