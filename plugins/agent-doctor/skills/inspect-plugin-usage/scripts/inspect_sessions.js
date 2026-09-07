#!/usr/bin/env node
// Summarize skill invocations without returning transcript content.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const readline = require('node:readline');
const { parseArgs } = require('node:util');

const SKILL_PATH = /([A-Za-z0-9_./~:-]+\/SKILL\.md)/g;
const ERROR = /permission denied|no such file|not found|access denied|\berror\b|\bfailed\b/i;
const KNOWN = {
  codex: new Set(['compacted', 'event_msg', 'inter_agent_communication_metadata', 'response_item', 'session_meta', 'token_usage_record', 'turn_context', 'world_state']),
  claude: new Set(['agent-name', 'assistant', 'attachment', 'custom-title', 'file-history-snapshot', 'last-prompt', 'permission-mode', 'pr-link', 'queue-operation', 'system', 'user']),
};
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const matches = (text, pattern) => [...text.matchAll(pattern)].map(match => match[1]);
const expandHome = value => value === '~' ? os.homedir() : value.startsWith('~/') ? path.join(os.homedir(), value.slice(2)) : value;

function resolveCwd(value) {
  if (typeof value !== 'string' || !value) return null;
  const absolute = path.resolve(expandHome(value));
  try { return fs.realpathSync(absolute); } catch (error) {
    if (!['ENOENT', 'ENOTDIR'].includes(error.code)) throw error;
    const parent = path.dirname(absolute);
    return parent === absolute ? absolute : path.join(resolveCwd(parent), path.basename(absolute));
  }
}

function increment(counter, client, category) {
  const key = `${client}:${category}`;
  counter.set(key, (counter.get(key) || 0) + 1);
}
function counterRows(counter) {
  return [...counter].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, count]) => {
    const [client, category] = key.split(':');
    return { client, category, count };
  });
}
function flatten(value, unwrap = false) {
  if (typeof value === 'string') {
    if (unwrap && value.trimStart().startsWith('{')) {
      try {
        const envelope = JSON.parse(value);
        if (isObject(envelope) && Object.hasOwn(envelope, 'output')) return flatten(envelope.output, true);
      } catch { /* Ordinary output may begin with an incomplete JSON object. */ }
    }
    return value;
  }
  if (Array.isArray(value) || isObject(value)) return Object.values(value).map(item => flatten(item, unwrap)).join('\n');
  return '';
}
function identityFromPath(value) {
  const normalized = value.replaceAll('\\', '/');
  for (const pattern of [/(?:^|\/)plugins\/cache\/[^/]+\/([^/]+)\/[^/]+\/skills\/([^/]+)\/SKILL\.md$/, /(?:^|\/)plugins\/([^/]+)\/skills\/([^/]+)\/SKILL\.md$/]) {
    const match = normalized.match(pattern);
    if (match) return match.slice(1);
  }
  const standalone = normalized.match(/(?:^|\/)(?:\.codex|\.claude)\/skills\/(?:\.system\/)?([^/]+)\/SKILL\.md$/);
  return standalone ? [null, standalone[1]] : null;
}
function identityFromName(value) {
  const name = value.replace(/^\//, '');
  const colon = name.indexOf(':');
  return colon < 0 ? [null, name] : [name.slice(0, colon), name.slice(colon + 1)];
}
function matchesTarget(identity, kind, name) {
  if (!identity) return false;
  const [plugin, skill] = identity;
  return (kind === 'plugin' ? plugin : plugin ? `${plugin}:${skill}` : skill) === name;
}
function initialRead(text, tool) {
  return ['Read', 'read_file'].includes(tool) || /\b(?:cat|head)\s+/.test(text) || /\bsed\s+-n\s+['"]?1(?:,|p\b)/.test(text);
}
function directRead(text, skillPath, tool) {
  if (['Read', 'read_file'].includes(tool)) return text.includes(skillPath);
  const escaped = skillPath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`\\b(?:cat|head)\\s+[^\\n;]{0,200}${escaped}`).test(text)
    || new RegExp(`\\bsed\\s+-n\\s+['"]?1(?:,|p\\b)[^\\n;]{0,240}${escaped}`).test(text);
}
function timestamp(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}(?:$|[T ])/.test(value)) return NaN;
  const zoned = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return Date.parse(zoned || value.length === 10 ? value : `${value}Z`);
}
function contentBlocks(record) {
  const content = record.message?.content;
  return Array.isArray(content) ? content.filter(isObject) : [];
}
function commandText(record) {
  if (record.type !== 'user' || record.isMeta !== true) return '';
  const content = record.message?.content;
  return typeof content === 'string' ? content : contentBlocks(record).filter(block => block.type === 'text' && typeof block.text === 'string').map(block => block.text).join('\n');
}

async function* readRecords(file, client, warnings) {
  const input = fs.createReadStream(file, { encoding: 'utf8' });
  const lines = readline.createInterface({ input, crlfDelay: Infinity });
  try {
    for await (const line of lines) {
      let record;
      try { record = JSON.parse(line); } catch { increment(warnings, client, 'malformed-json'); continue; }
      if (!isObject(record)) continue;
      if (!KNOWN[client].has(record.type)) increment(warnings, client, 'unknown-record');
      yield record;
    }
  } catch { increment(warnings, client, 'unreadable-session'); }
  finally { lines.close(); input.destroy(); }
}
function sessionFiles(root) {
  const files = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const file = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...sessionFiles(file));
    else if (entry.name.endsWith('.jsonl')) files.push(file);
  }
  return files.sort();
}
async function scan(root, client, kind, name, start, end, warnings) {
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    increment(warnings, client, 'missing-session-root');
    return [];
  }
  const sessions = [];
  for (const file of sessionFiles(root)) {
    let cwd = null, inWindow = false;
    const results = new Map(), calls = [], invocations = [];
    for await (const record of readRecords(file, client, warnings)) {
      const time = timestamp(record.timestamp);
      const selected = time >= start && time <= end;
      inWindow ||= selected;
      if (client === 'codex') {
        const payload = record.payload;
        if (!isObject(payload)) continue;
        if (record.type === 'session_meta' && cwd === null) cwd = resolveCwd(payload.cwd);
        if (record.type !== 'response_item') continue;
        if (['custom_tool_call_output', 'function_call_output'].includes(payload.type)) {
          if (payload.call_id) {
            const text = flatten(payload.output, true);
            results.set(String(payload.call_id), { names: new Set(matches(text, /^name:\s*(\S+)\s*$/gm)), paths: new Set(matches(text, SKILL_PATH)), error: ERROR.test(text) });
          }
          continue;
        }
        if (!selected || !['custom_tool_call', 'function_call'].includes(payload.type)) continue;
        const text = flatten(Object.hasOwn(payload, 'input') ? payload.input : payload.arguments ?? '');
        if (!initialRead(text, payload.name)) continue;
        const paths = [...new Set(matches(text, SKILL_PATH))].sort();
        for (const skillPath of paths) {
          const identity = identityFromPath(skillPath);
          if (matchesTarget(identity, kind, name)) calls.push({ id: String(payload.call_id), skillPath, skillName: identity[1], direct: directRead(text, skillPath, payload.name), single: paths.length === 1 });
        }
      } else {
        cwd ??= resolveCwd(record.cwd);
        const blocks = contentBlocks(record);
        for (const block of blocks) if (block.type === 'tool_result' && block.tool_use_id) results.set(String(block.tool_use_id), Boolean(block.is_error));
        if (!selected) continue;
        for (const block of blocks) {
          if (block.type !== 'tool_use' || block.name !== 'Skill') continue;
          const skillName = isObject(block.input) ? block.input.skill : null;
          if (typeof skillName !== 'string') { increment(warnings, client, 'unsupported-skill-record'); continue; }
          if (matchesTarget(identityFromName(skillName), kind, name)) calls.push({ id: String(block.id ?? '') });
        }
        for (const command of matches(commandText(record), /<command-name>\/?([^<]+)<\/command-name>/g)) {
          if (matchesTarget(identityFromName(command.trim()), kind, name)) invocations.push({ status: 'successful', category: null });
        }
      }
    }
    if (!inWindow) continue;
    if (cwd === null) increment(warnings, client, 'missing-session-cwd');
    for (const call of calls) {
      let status = 'incomplete', category = null;
      const result = results.get(call.id);
      if (client === 'codex') {
        if (result?.names.has(call.skillName)) status = 'successful';
        else if (call.direct && (call.single || result?.paths.has(call.skillPath)) && result?.error) { status = 'problem'; category = 'skill-load-error'; }
        if (status === 'incomplete' && !call.direct) continue;
      } else if (results.has(call.id)) {
        status = result ? 'problem' : 'successful';
        category = result ? 'skill-error' : null;
      }
      invocations.push({ status, category });
    }
    sessions.push({ client, cwd, invocations });
  }
  return sessions;
}
function emptyCounts() {
  return { attempts: 0, successful: 0, problems: 0, incomplete: 0, scanned_sessions: 0, matched_sessions: 0 };
}
function summarize(sessions) {
  const clients = { codex: emptyCounts(), claude: emptyCounts() }, categories = new Map();
  for (const session of sessions) {
    const counts = clients[session.client];
    counts.scanned_sessions++;
    if (session.invocations.length) counts.matched_sessions++;
    for (const invocation of session.invocations) {
      counts.attempts++;
      counts[invocation.status === 'problem' ? 'problems' : invocation.status]++;
      if (invocation.category) increment(categories, session.client, invocation.category);
    }
  }
  const combined = emptyCounts();
  for (const key of Object.keys(combined)) combined[key] = clients.codex[key] + clients.claude[key];
  return { combined, clients, problem_categories: counterRows(categories) };
}
async function analyze({ target_kind, target_name, project = null, days, now = new Date(), codex_home, claude_home }) {
  if (!['plugin', 'skill'].includes(target_kind)) throw new Error("target_kind must be 'plugin' or 'skill'");
  if (!target_name) throw new Error('target_name must not be empty');
  if (!Number.isInteger(days) || days <= 0) throw new Error('days must be positive');
  const end = new Date(now), start = new Date(end.getTime() - days * 86400000);
  const resolvedProject = resolveCwd(project);
  const warnings = new Map();
  const sessions = [
    ...await scan(path.join(expandHome(codex_home ?? process.env.CODEX_HOME ?? '~/.codex'), 'sessions'), 'codex', target_kind, target_name, start, end, warnings),
    ...await scan(path.join(expandHome(claude_home ?? process.env.CLAUDE_CONFIG_DIR ?? '~/.claude'), 'projects'), 'claude', target_kind, target_name, start, end, warnings),
  ];
  const scopes = { all: summarize(sessions) };
  if (resolvedProject !== null) scopes.project = summarize(sessions.filter(session => session.cwd !== null && (session.cwd === resolvedProject || session.cwd.startsWith(`${resolvedProject}${resolvedProject.endsWith(path.sep) ? '' : path.sep}`))));
  const format = value => value.toISOString().replace('.000Z', 'Z').replace(/\.(\d{3})Z$/, '.$1000Z');
  return { target: { kind: target_kind, name: target_name }, window: { days, start: format(start), end: format(end) }, project: resolvedProject, scopes, warnings: counterRows(warnings) };
}
function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (isObject(value)) return Object.fromEntries(Object.keys(value).sort().map(key => [key, sorted(value[key])]));
  return value;
}
async function main() {
  const { values } = parseArgs({ options: { plugin: { type: 'string' }, skill: { type: 'string' }, project: { type: 'string' }, days: { type: 'string', default: '30' }, help: { type: 'boolean', short: 'h' } } });
  if (values.help) { console.log('Summarize recent Codex and Claude skill invocations.\nUsage: inspect_sessions.js (--plugin NAME | --skill NAME) [--project PATH] [--days N]'); return; }
  if (Object.hasOwn(values, 'plugin') === Object.hasOwn(values, 'skill')) throw new Error('provide exactly one of --plugin or --skill');
  if (!/^[+]?[0-9]+$/.test(values.days)) throw new Error('days must be positive');
  const report = await analyze({ target_kind: Object.hasOwn(values, 'plugin') ? 'plugin' : 'skill', target_name: values.plugin ?? values.skill, project: values.project, days: Number(values.days) });
  console.log(JSON.stringify(sorted(report), null, 2));
}
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 2; });
module.exports = { analyze };
