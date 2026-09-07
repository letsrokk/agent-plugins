import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {hash, invalid, PapercutsError} from './models.js';

export function resolveClient(explicit, environ = process.env) {
  const client = explicit ?? environ.PAPERCUTS_CLIENT ?? 'codex';
  if (!['codex', 'claude'].includes(client)) throw new PapercutsError(explicit === undefined ? 'invalid_config' : 'usage', 'Client must be codex or claude');
  return client;
}
export function discoverProject(cwd) {
  const result = spawnSync('git', ['-C', cwd, 'rev-parse', '--show-toplevel'], {encoding: 'utf8'});
  if (result.error && result.error.code !== 'ENOENT') throw result.error;
  if (result.status !== 0) return [cwd, null];
  const root = result.stdout.trim();
  const remote = spawnSync('git', ['-C', root, 'config', '--get', 'remote.origin.url'], {encoding: 'utf8'});
  if (remote.error && remote.error.code !== 'ENOENT') throw remote.error;
  return [root, remote.status === 0 ? remote.stdout.trim() || null : null];
}
export function projectRef(root, remote) {
  let identity = fs.realpathSync(root);
  if (remote) {
    let host, pathname;
    const scp = remote.trim().match(/^[^/@\s]+@([^/:\s]+):(.*)$/);
    if (scp) [, host, pathname] = scp;
    else { try { const url = new URL(remote.trim()); host = url.hostname; pathname = url.pathname; } catch {} }
    if (host) {
      pathname = pathname.split(/[?#]/)[0].replace(/\/+$/, '').replace(/\.git$/, '').replace(/^\/+|\/+$/g, '');
      identity = host.toLowerCase() + (pathname ? `/${pathname}` : '');
    }
  }
  return {id: `prj_${hash(identity).slice(0,16)}`, name: path.basename(fs.realpathSync(root))};
}
function readConfig(file) {
  let fd;
  try {
    const expected = fs.lstatSync(file);
    if (!expected.isFile() || expected.size > 1048576) throw new Error('unsafe configuration');
    fd = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0) | (fs.constants.O_NONBLOCK || 0));
    const actual = fs.fstatSync(fd);
    if (!actual.isFile() || actual.dev !== expected.dev || actual.ino !== expected.ino || actual.size > 1048576) throw new Error('unsafe configuration');
    const config = JSON.parse(fs.readFileSync(fd, 'utf8'));
    if (!config || config.scope !== 'user' || Object.keys(config).some(k => k !== 'scope')) throw new Error('obsolete configuration');
    return file;
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    if (['EACCES','EPERM','EROFS'].includes(error.code)) throw error;
    throw new PapercutsError('invalid_config', `Unsupported Papercuts configuration: ${file}. Only user journals are supported; migrate old data manually before removing this configuration.`);
  } finally { if (fd !== undefined) fs.closeSync(fd); }
}
export function resolveStorage(cwd, {client = resolveClient(), environ = process.env, home = os.homedir(), project_root, remote_url} = {}) {
  if (!['codex','claude'].includes(client)) throw invalid('Client must be codex or claude');
  if (Object.hasOwn(environ, 'PAPERCUTS_FILE')) throw new PapercutsError('invalid_config', 'PAPERCUTS_FILE is no longer supported. Migrate the old journal manually before removing this setting.');
  const [discoveredRoot, discoveredRemote] = project_root === undefined || remote_url === undefined ? discoverProject(cwd) : [project_root, remote_url];
  const root = project_root ?? discoveredRoot;
  const resolvedHome = fs.realpathSync(home);
  const projectConfig = readConfig(path.join(root, `.${client}`, 'papercuts.config.json'));
  const userConfig = readConfig(path.join(resolvedHome, `.${client}`, 'papercuts.config.json'));
  return {project: projectRef(root, remote_url ?? discoveredRemote), project_root: root, home: resolvedHome, journal_path: path.join(resolvedHome, `.${client}`, 'papercuts.jsonl'), scope: 'user', config_source: projectConfig ?? userConfig, client};
}
