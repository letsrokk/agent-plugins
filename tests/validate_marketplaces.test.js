'use strict';

const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { validateRepository } = require('../scripts/validate_marketplaces.js');

let root;
function write(relativePath, text) {
  const file = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}
const writeJson = (file, payload) => write(file, JSON.stringify(payload));
const codexEntry = (name, source = `./plugins/${name}`) => ({
  name, source: { source: 'local', path: source },
  policy: { installation: 'AVAILABLE', authentication: 'ON_INSTALL' }, category: 'Developer Tools',
});
const claudeEntry = (name, source = `./plugins/${name}`) => ({ name, source });
function writeCatalogs(codexPlugins = [], claudePlugins = []) {
  writeJson('.agents/plugins/marketplace.json', {
    name: 'rokk-club-codex-plugins', interface: { displayName: 'Rokk Club Codex Plugins' }, plugins: codexPlugins,
  });
  writeJson('.claude-plugin/marketplace.json', {
    $schema: 'https://json.schemastore.org/claude-code-marketplace.json',
    name: 'rokk-club-claude-plugins', owner: { name: 'Rokk Club' }, plugins: claudePlugins,
  });
}
function writePortableManifest(name, version = '0.1.0') {
  writeJson(`plugins/${name}/plugin.json`, {
    $schema: 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', name, version,
  });
}
function writeCodexManifest(name, version = '0.1.0', skills = true) {
  writeJson(`plugins/${name}/.codex-plugin/plugin.json`, {
    name, version, ...(skills ? { skills: './skills/' } : {}),
  });
}
function writeSkill(plugin, skill = plugin, frontmatterName = skill) {
  write(`plugins/${plugin}/skills/${skill}/SKILL.md`,
    `---\nname: ${frontmatterName}\ndescription: Test skill.\n---\n\n# Test skill\n`);
}
function writeAdaptedPackage(name, { includeNotice = true, missingAgent = null } = {}) {
  const title = name === 'code-simplifier' ? 'Code Simplifier' : 'PR Review Toolkit';
  writeJson(`plugins/${name}/plugin.json`, {
    $schema: 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', name, version: '0.1.0',
    description: 'Review and simplify code.', author: { name: 'Rokk Club' },
    homepage: 'https://github.com/letsrokk/agent-plugins', repository: 'https://github.com/letsrokk/agent-plugins',
    license: 'Apache-2.0', keywords: ['codex', 'code-quality'],
  });
  writeCodexManifest(name);
  const skill = `plugins/${name}/skills/${name}`;
  write(`${skill}/SKILL.md`, `---\nname: ${name}\ndescription: Test skill.\n---\n\n# ${title}\n\nAdapted from Anthropic's ${title}.\n`
    + (name === 'code-simplifier' ? 'Dispatch `code_simplifier_agent`.\n' : ''));
  write(`${skill}/agents/openai.yaml`, `interface:\n  display_name: "${title}"\n`);
  const agents = name === 'code-simplifier' ? ['code_simplifier_agent'] : [
    'pr_review_toolkit_code_reviewer', 'pr_review_toolkit_code_simplifier',
    'pr_review_toolkit_comment_analyzer', 'pr_review_toolkit_pr_test_analyzer',
    'pr_review_toolkit_silent_failure_hunter', 'pr_review_toolkit_type_design_analyzer',
  ];
  for (const agent of agents) {
    if (agent === missingAgent) continue;
    write(`${skill}/agents/${agent}.toml`, `# Adapted from Anthropic's ${title} for Codex.\n`
      + `name = "${agent}"\ndescription = "Reviews code."\ndeveloper_instructions = "Preserve behavior."\n`);
  }
  write(`plugins/${name}/LICENSE`, 'Apache License\nVersion 2.0, January 2004\n');
  if (includeNotice) write(`plugins/${name}/NOTICE`, `${title} includes modified material from Anthropic's ${title}.\n`
    + `https://github.com/anthropics/claude-plugins-official/tree/main/plugins/${name}\nRokk Club adapted it from Claude Code for Codex.\n`);
}
const hasError = (errors, text) => assert.ok(errors.some(error => error.includes(text)), `Missing ${JSON.stringify(text)} in ${JSON.stringify(errors)}`);

beforeEach(() => {
  root = fs.mkdtempSync(path.join(os.tmpdir(), 'marketplace-validation-'));
  writeCatalogs();
  write('AGENTS.md', '# Agent guidelines\n');
  fs.symlinkSync('AGENTS.md', path.join(root, 'CLAUDE.md'));
});
afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

test('accepts empty marketplaces and agents symlink', () => {
  assert.deepEqual(validateRepository(root), []);
});

test('rejects duplicate plugin names', () => {
  const entry = codexEntry('duplicate');
  writeCatalogs([entry, entry]);
  writePortableManifest('duplicate');
  hasError(validateRepository(root), "duplicate plugin name 'duplicate'");
});

test('rejects source path that can escape plugins directory', () => {
  writeCatalogs([codexEntry('unsafe', './plugins/../unsafe')]);
  hasError(validateRepository(root), "must be './plugins/unsafe'");
});

test('rejects Codex entry without required policy and category', () => {
  writeCatalogs([{ name: 'incomplete', source: { source: 'local', path: './plugins/incomplete' } }]);
  writePortableManifest('incomplete');
  const errors = validateRepository(root);
  hasError(errors, "policy.installation must be 'AVAILABLE'");
  hasError(errors, "policy.authentication must be 'ON_INSTALL'");
  hasError(errors, 'category must be a non-empty string');
});

test('rejects plugin without portable manifest', () => {
  writeCatalogs([codexEntry('missing-manifest')]);
  fs.mkdirSync(path.join(root, 'plugins/missing-manifest'), { recursive: true });
  hasError(validateRepository(root), 'missing portable manifest');
});

test('rejects Claude plugin without compatibility manifest', () => {
  writeCatalogs([], [claudeEntry('claude-ready')]);
  writePortableManifest('claude-ready');
  hasError(validateRepository(root), 'missing Claude compatibility manifest');
});

test('rejects Claude file instead of agents symlink', () => {
  fs.unlinkSync(path.join(root, 'CLAUDE.md'));
  write('CLAUDE.md', '# Duplicate instructions\n');
  assert.ok(validateRepository(root).includes('CLAUDE.md must be a symlink to AGENTS.md'));
});

for (const name of ['code-simplifier', 'pr-review-toolkit']) {
  test(`accepts complete ${name} package`, () => {
    writeCatalogs([codexEntry(name)]);
    writeAdaptedPackage(name);
    assert.deepEqual(validateRepository(root), []);
  });
}

test('accepts Codex package with matching compatibility manifest', () => {
  writeCatalogs([codexEntry('complete')]);
  writePortableManifest('complete');
  writeCodexManifest('complete');
  writeSkill('complete');
  assert.deepEqual(validateRepository(root), []);
});

test('rejects inconsistent Codex compatibility manifest', () => {
  writeCatalogs([codexEntry('inconsistent')]);
  writePortableManifest('inconsistent', '1.2.3');
  writeJson('plugins/inconsistent/.codex-plugin/plugin.json', { name: 'other', version: '1.2.2' });
  writeSkill('inconsistent');
  const errors = validateRepository(root);
  hasError(errors, "name must match catalog entry 'inconsistent'");
  hasError(errors, "version must match portable manifest '1.2.3'");
  hasError(errors, "skills must be './skills/'");
});

test('rejects unknown portable manifest field', () => {
  writeCatalogs([codexEntry('unknown-field')]);
  writeJson('plugins/unknown-field/plugin.json', {
    $schema: 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', name: 'unknown-field', skills: './skills/',
  });
  writeSkill('unknown-field');
  hasError(validateRepository(root), "unknown field 'skills'");
});

test('Codex native components require native manifest selection', () => {
  const name = 'native-components';
  writeCatalogs([codexEntry(name)]);
  writeSkill(name);
  for (const [field, value] of [['hooks', './hooks/hooks.json'], ['mcpServers', { server: { command: 'node' } }]]) {
    writePortableManifest(name);
    writeJson(`plugins/${name}/.codex-plugin/plugin.json`, { name, version: '0.1.0', skills: './skills/', [field]: value });
    hasError(validateRepository(root), 'omit $schema');
    writeJson(`plugins/${name}/plugin.json`, { name, version: '0.1.0' });
    assert.deepEqual(validateRepository(root), []);
  }
});

test('schema omission requires a native manifest', () => {
  writeCatalogs([], [claudeEntry('native')]);
  writeSkill('native');
  writeJson('plugins/native/plugin.json', { name: 'native', version: '0.1.0' });
  hasError(validateRepository(root), '$schema');
  writeJson('plugins/native/.claude-plugin/plugin.json', { name: 'native', version: '0.1.0' });
  assert.deepEqual(validateRepository(root), []);
});

test('rejects plugin without discoverable component', () => {
  writeCatalogs([codexEntry('empty-plugin')]);
  writePortableManifest('empty-plugin');
  hasError(validateRepository(root), 'must provide at least one skill or mcp.json');
});

test('scripted plugin requires test and validation entrypoints', () => {
  write('plugins/scripted/src/scripted.js', "'use strict';\n");
  const errors = validateRepository(root);
  hasError(errors, 'scripts/test.js is missing');
  hasError(errors, 'scripts/validate.js is missing');
  write('plugins/scripted/scripts/test.js', "'use strict';\n");
  write('plugins/scripted/scripts/validate.js', "'use strict';\n");
  assert.deepEqual(validateRepository(root), []);
});

test('rejects skill name that differs from directory', () => {
  writeCatalogs([codexEntry('bad-skill')]);
  writePortableManifest('bad-skill');
  writeSkill('bad-skill', 'expected-name', 'different-name');
  hasError(validateRepository(root), "skill name must match directory 'expected-name'");
});

test('enforces skill file prompt size limit', () => {
  writeCatalogs([codexEntry('large-skill')]);
  writePortableManifest('large-skill');
  writeCodexManifest('large-skill');
  writeSkill('large-skill');
  const file = path.join(root, 'plugins/large-skill/skills/large-skill/SKILL.md');
  const padded = Buffer.alloc(7168, 'x');
  fs.readFileSync(file).copy(padded);
  fs.writeFileSync(file, padded);
  assert.deepEqual(validateRepository(root), []);
  fs.appendFileSync(file, 'x');
  hasError(validateRepository(root), 'must not exceed 7168 bytes');
});

test('rejects malformed custom agent TOML', () => {
  writeCatalogs([codexEntry('bad-agent')]);
  writePortableManifest('bad-agent');
  writeSkill('bad-agent');
  write('plugins/bad-agent/skills/bad-agent/agents/bad_agent.toml', 'name = "unterminated\n');
  hasError(validateRepository(root), 'invalid TOML');
});

test('rejects custom agent name that differs from filename', () => {
  writeCatalogs([codexEntry('bad-agent-name')]);
  writePortableManifest('bad-agent-name');
  writeSkill('bad-agent-name');
  write('plugins/bad-agent-name/skills/bad-agent-name/agents/expected_agent.toml', 'name = "different_agent"\n');
  hasError(validateRepository(root), "agent name must match filename 'expected_agent'");
});

test('rejects non-MIT plugin without package license', () => {
  writeCatalogs([codexEntry('apache-plugin')]);
  writeJson('plugins/apache-plugin/plugin.json', {
    $schema: 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', name: 'apache-plugin', license: 'Apache-2.0',
  });
  writeSkill('apache-plugin');
  hasError(validateRepository(root), 'declares Apache-2.0 but has no package LICENSE');
});

test('rejects code-simplifier without attribution notice', () => {
  writeCatalogs([codexEntry('code-simplifier')]);
  writeAdaptedPackage('code-simplifier', { includeNotice: false });
  hasError(validateRepository(root), 'code-simplifier/NOTICE is missing');
});

test('rejects code-simplifier without custom agent', () => {
  writeCatalogs([codexEntry('code-simplifier')]);
  writeAdaptedPackage('code-simplifier', { missingAgent: 'code_simplifier_agent' });
  hasError(validateRepository(root), 'code_simplifier_agent.toml is missing');
});

test('rejects PR Review Toolkit without required agent', () => {
  const missing = 'pr_review_toolkit_type_design_analyzer';
  writeCatalogs([codexEntry('pr-review-toolkit')]);
  writeAdaptedPackage('pr-review-toolkit', { missingAgent: missing });
  hasError(validateRepository(root), `${missing}.toml is missing`);
});
