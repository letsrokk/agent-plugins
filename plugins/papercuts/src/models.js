import fs from 'node:fs';
import crypto from 'node:crypto';
import casefoldExceptions from './casefold.js';

export class PapercutsError extends Error {
  constructor(code, message, {retryable = false, suggested_fix = null} = {}) {
    super(message); Object.assign(this, {code, retryable, suggested_fix});
  }
}
export const invalid = message => new PapercutsError('invalid_input', message);
export function publicError(error) {
  if (error instanceof PapercutsError) return error;
  if (['EACCES', 'EPERM', 'EROFS'].includes(error.code)) return new PapercutsError('permission_denied', error.message);
  if (typeof error.code === 'string' && /^E[A-Z]+$/.test(error.code)) return new PapercutsError('io_failure', error.message, {retryable: true});
  return new PapercutsError('internal_failure', error.message || 'Unexpected failure');
}
export function errorResult(error) {
  const {code, message, retryable, suggested_fix} = publicError(error);
  return {ok: false, error: {code, message, retryable, suggested_fix}};
}
export const hash = value => crypto.createHash('sha256').update(value).digest('hex');
export function compareUnicode(a,b) {
  const left = [...a], right = [...b];
  for (let i = 0; i < Math.min(left.length,right.length); i++) {
    const difference = left[i].codePointAt(0)-right[i].codePointAt(0);
    if (difference) return difference;
  }
  return left.length-right.length;
}
export const casefold = value => [...value].map(char => casefoldExceptions[char] ?? char.toLowerCase()).join('');
export function stableJSON(value) {
  if (Array.isArray(value)) return `[${value.map(stableJSON).join(',')}]`;
  if (value !== null && typeof value === 'object') return `{${Object.keys(value).sort(compareUnicode).map(k => `${JSON.stringify(k)}:${stableJSON(value[k])}`).join(',')}}`;
  if (typeof value === 'number' && !Number.isFinite(value)) throw invalid('Non-finite number is not JSON');
  return JSON.stringify(value);
}
export const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const program = String.raw`(?<![A-Za-z0-9_.~])/(?=[^/\r\n]*(?:[\^$*+?()[{|\\]|\.(?:[*+?]|/)))(?:\\.|[^/\\\r\n])+/[adgimpsuvxy]*(?=$|[\s"'\x60{(;|&)\]}])`;
const posix = new RegExp(`(?<program>${program})|(?<path>(?<![A-Za-z0-9.:/~])/(?!/)[^\\s"']*)`, 'g');
function locations(value, pattern, replacement, preserve = false) {
  return value.replace(pattern, (...args) => {
    const match = args[0], groups = args.at(-1);
    if (isObject(groups) && groups.program !== undefined) return match;
    if (preserve && /^(?:[A-Z]:[\\/]|\/[A-Z]\/)\.\.\.$/i.test(match.replace(/[,;:!?)\]}]+$/, ''))) return match;
    return replacement + match.slice(match.replace(/[.,;:!?)\]}]+$/, '').length);
  });
}
export function sanitizeString(value, field = 'evidence') {
  if (typeof value !== 'string') throw invalid(`${field} must be a string`);
  const lines = value.replaceAll('\0', '\n').split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  if (lines.filter(s => /^(?:(?:export|declare\s+-x|typeset\s+-x)\s+)?[A-Za-z_][A-Za-z0-9_]*=.*$/.test(s)).length >= 2 || /^(?:os\.)?(?:env|environ|environment)\s*(?:\(|=|:)\s*\{/is.test(value.trimStart())) throw invalid('raw environment evidence is not allowed');
  let parsed; try { parsed = JSON.parse(value); } catch {}
  if (isObject(parsed)) {
    const keys = Object.keys(parsed);
    if (keys.length >= 2 && keys.every(k => /^[A-Za-z_][A-Za-z0-9_]*$/.test(k)) && (keys.filter(k => k.toUpperCase() === k).length >= 2 || keys.filter(k => ['home','path','pwd','shell','temp','tmp','user','userprofile'].includes(k.toLowerCase())).length >= 2)) throw invalid('raw environment evidence is not allowed');
  }
  let result = value.replace(/((?<![A-Za-z0-9_.-])["']?(?=[A-Za-z_])[A-Za-z0-9_.-]*(?:TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY(?:_ID)?|JWT)[A-Za-z0-9_.-]*["']?\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)/gi, '$1[REDACTED]')
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, 'Bearer [REDACTED]')
    .replace(/\b([a-z][a-z0-9+.-]*:\/\/)[^/\s:@]+(?::[^/\s@]*)?@/gi, '$1[REDACTED]@')
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b/g, '[REDACTED]')
    .replace(/\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b/g, '[REDACTED]');
  result = locations(result, /\b(?:https?|ssh|git|ftp|file):\/\/[^\s"']+/gi, '[REDACTED_URL]');
  result = locations(result, /(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+@[A-Za-z0-9.-]+|[A-Za-z0-9.-]+\.[A-Za-z]{2,}):(?=[^\s"']*[\\/])[^\s"']+/gi, '[REDACTED_URL]');
  result = locations(result, /(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s"']+/gi, '[REDACTED_PATH]', true);
  return locations(result, posix, '[REDACTED_PATH]', true);
}
function readEvidence(file) {
  if (typeof file !== 'string') throw invalid('stderr_file must be a path');
  let fd;
  try {
    const expected = fs.lstatSync(file);
    if (!expected.isFile() || expected.size > 1048576) throw invalid('stderr_file must be a regular file no larger than 1 MiB');
    fd = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0) | (fs.constants.O_NONBLOCK || 0));
    const actual = fs.fstatSync(fd);
    if (!actual.isFile() || actual.size > 1048576 || expected.ino !== actual.ino || expected.dev !== actual.dev) throw invalid('stderr_file could not be read safely');
    const buffer = Buffer.alloc(1048577); let length = 0, n;
    while (length < buffer.length && (n = fs.readSync(fd, buffer, length, buffer.length - length, null))) length += n;
    if (length > 1048576) throw invalid('stderr_file exceeds 1 MiB');
    return new TextDecoder('utf-8', {fatal: true}).decode(buffer.subarray(0, length));
  } catch (error) { if (error instanceof PapercutsError) throw error; throw invalid('stderr_file could not be read safely as UTF-8'); }
  finally { if (fd !== undefined) fs.closeSync(fd); }
}
export function sanitizeContext(context = {}) {
  if (context === null) return {};
  if (!isObject(context) || Object.keys(context).some(k => !['command','exit_status','stderr','stderr_file','note'].includes(k))) throw invalid('context contains unsupported evidence fields');
  if ('stderr' in context && 'stderr_file' in context) throw invalid('provide stderr or stderr_file, not both');
  const result = {};
  for (const [key, limit] of [['command',1024], ['note',2048]]) if (key in context) {
    const value = sanitizeString(context[key], key);
    if ([...value].length > limit) throw invalid(`${key} exceeds ${limit} characters`);
    result[key] = value;
  }
  if ('exit_status' in context) {
    if (!Number.isSafeInteger(context.exit_status)) throw invalid('exit_status must be an integer');
    result.exit_status = context.exit_status;
  }
  if ('stderr' in context || 'stderr_file' in context) {
    const value = sanitizeString('stderr' in context ? context.stderr : readEvidence(context.stderr_file), 'stderr');
    if (Buffer.byteLength(value) > 4096) throw invalid('stderr exceeds 4096 UTF-8 bytes');
    result.stderr = value;
  }
  return result;
}
