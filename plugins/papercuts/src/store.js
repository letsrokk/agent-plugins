import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {hash, stableJSON, isObject, nonempty, invalid, PapercutsError} from './models.js';

const C = fs.constants;
const malformed = (file, line, detail = '') => new PapercutsError('malformed_journal', `Malformed journal event at ${file}:${line}${detail ? ` (${detail})` : ''}`);
const unsafe = file => invalid(`Storage must use private, user-owned real directories and regular files: ${file}`);
const uid = () => process.getuid?.();
function owned(stat) { return uid() === undefined || stat.uid === uid(); }
function privateDirectory(directory, create = false, home = false) {
  if (create) { try { fs.mkdirSync(directory, {mode: 0o700}); } catch (e) { if (e.code !== 'EEXIST') throw e; } }
  const stat = fs.lstatSync(directory);
  if (!stat.isDirectory() || !owned(stat) || (process.platform !== 'win32' && (stat.mode & (home ? 0o022 : 0o077)))) throw unsafe(directory);
  return stat;
}
function same(a,b) { return a.dev === b.dev && a.ino === b.ino; }
function regular(file, flags, {create = false, exclusive = false, missing = false} = {}) {
  let expected;
  try { expected = fs.lstatSync(file); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  if (expected && (!expected.isFile() || !owned(expected) || expected.nlink !== 1 || (process.platform !== 'win32' && (expected.mode & 0o077)))) throw unsafe(file);
  let fd;
  try {
    const additions = (C.O_NOFOLLOW || 0) | (C.O_NONBLOCK || 0) | (create ? C.O_CREAT : 0) | (exclusive || (create && !expected) ? C.O_EXCL : 0);
    fd = fs.openSync(file, flags | additions, 0o600);
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || !owned(stat) || stat.nlink !== 1 || (expected && !same(stat, expected)) || (process.platform !== 'win32' && (stat.mode & 0o077))) throw unsafe(file);
    return fd;
  } catch (e) {
    if (fd !== undefined) fs.closeSync(fd);
    if (e.code === 'ENOENT' && missing) return null;
    if (['ELOOP','ENOTDIR'].includes(e.code)) throw unsafe(file);
    throw e;
  }
}
function syncDirectory(directory) {
  if (process.platform === 'win32') return;
  const fd = fs.openSync(directory, C.O_RDONLY | (C.O_DIRECTORY || 0) | (C.O_NOFOLLOW || 0));
  try { fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
function writeFile(file, data) {
  const fd = regular(file, C.O_WRONLY, {create: true, exclusive: true});
  try { fs.writeFileSync(fd, data); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
export function validateEvent(event, file = '<events>', line = 1) {
  if (!isObject(event) || event.contract !== 1 || !['complaint','encounter','resolved','reopened'].includes(event.kind) || !nonempty(event.ts) || !nonempty(event.agent) || !isObject(event.project) || !nonempty(event.project.id) || !nonempty(event.project.name)) throw malformed(file,line);
  let valid;
  if (event.kind === 'complaint') valid = nonempty(event.id) && nonempty(event.text) && ['minor','major','blocker'].includes(event.severity) && Array.isArray(event.tags) && event.tags.length <= 10 && event.tags.every(nonempty) && isObject(event.context);
  else valid = nonempty(event.complaint_id) && (event.note == null || nonempty(event.note)) && (event.kind !== 'encounter' || isObject(event.context));
  if (!valid) throw malformed(file,line);
}
export function foldEvents(events, file = '<events>') {
  const records = new Map();
  events.forEach((event, index) => {
    validateEvent(event,file,index+1);
    if (event.kind === 'complaint') {
      if (records.has(event.id)) throw malformed(file,index+1,'duplicate complaint ID');
      records.set(event.id, {...event, status:'open', encounter_count:1, vote_count:0, last_encounter_at:event.ts, resolution_note:null, recent_encounters:[], status_history:[]});
    } else {
      const record = records.get(event.complaint_id);
      if (!record) throw malformed(file,index+1,'orphan event');
      if (record.project.id !== event.project.id) throw malformed(file,index+1,'mismatched project ID');
      if (event.kind === 'encounter') {
        record.encounter_count++; record.vote_count++; record.last_encounter_at = event.ts;
        record.recent_encounters = [...record.recent_encounters,event].slice(-10);
      } else {
        record.status = event.kind === 'resolved' ? 'resolved' : 'open';
        if (event.kind === 'resolved') record.resolution_note = event.note ?? null;
        record.status_history.push(event);
      }
    }
  });
  return records;
}
export function serializeEvents(events) {
  events.forEach((event,index) => validateEvent(event,'<events>',index+1));
  return Buffer.from(events.map(e => stableJSON(e) + '\n').join(''));
}
export class JournalStore {
  constructor(storage) {
    this.path = storage.journal_path; this.home = storage.home; this.directory = path.dirname(this.path); this.lockPath = this.path + '.lock';
    if (this.path !== path.join(this.home, `.${storage.client}`, 'papercuts.jsonl') || !['codex','claude'].includes(storage.client)) throw unsafe(this.path);
  }
  check(create = false) {
    privateDirectory(this.home, false, true);
    // ponytail: private user storage limits path races; use native directory-relative I/O if shared storage returns.
    const homeParent = path.dirname(this.home);
    let ancestor = homeParent;
    while (true) {
      const stat = fs.lstatSync(ancestor);
      if (!stat.isDirectory() || (process.platform !== 'win32' && (stat.mode & 0o022) && !(stat.mode & 0o1000))) throw unsafe(ancestor);
      const next = path.dirname(ancestor); if (next === ancestor) break; ancestor = next;
    }
    const stat = privateDirectory(this.directory, create, true);
    if (this.parentIdentity && !same(stat, this.parentIdentity)) throw unsafe(this.directory);
  }
  bytes() {
    try {
      this.check(); const fd = regular(this.path,C.O_RDONLY,{missing:true});
      if (fd === null) return Buffer.alloc(0);
      try { return fs.readFileSync(fd); } finally { fs.closeSync(fd); }
    } catch (e) { if (e.code === 'ENOENT') return Buffer.alloc(0); throw e; }
  }
  parse(data) {
    const end = data.lastIndexOf(10) + 1;
    const tail = end !== data.length;
    const events = [];
    if (end) {
      let decoded; try { decoded = new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(0,end)); } catch { throw malformed(this.path,1,'invalid UTF-8'); }
      decoded.slice(0,-1).split('\n').forEach((line,index) => {
        let event; try { event = JSON.parse(line); } catch { throw malformed(this.path,index+1); }
        validateEvent(event,this.path,index+1); events.push(event);
      });
    }
    return {events, tail};
  }
  readEvents() { return this.parse(this.bytes()).events; }
  snapshot() { const data = this.bytes(); return {events:this.parse(data).events, digest:hash(data)}; }
  lockMetadata() {
    try {
      privateDirectory(this.lockPath);
      const fd = regular(path.join(this.lockPath,'owner.json'),C.O_RDONLY,{missing:true});
      if (fd === null) return null;
      try { const value = JSON.parse(fs.readFileSync(fd,'utf8')); return isObject(value) ? value : null; } finally { fs.closeSync(fd); }
    } catch (e) { if (e.code === 'ENOENT' || e instanceof SyntaxError) return null; throw e; }
  }
  removeLock(token) {
    this.check();
    try {
      const before = fs.lstatSync(this.lockPath);
      if (this.lockMetadata()?.token !== token || !same(before,fs.lstatSync(this.lockPath))) return;
      fs.unlinkSync(path.join(this.lockPath,'owner.json')); fs.rmdirSync(this.lockPath);
    } catch (error) {
      if (!['ENOENT','ENOTEMPTY','EEXIST'].includes(error.code)) throw error;
    }
  }
  acquireLock() {
    const token = crypto.randomUUID(); const deadline = performance.now()+5000;
    while (true) {
      this.check(true);
      try { fs.mkdirSync(this.lockPath,{mode:0o700}); break; }
      catch (e) {
        if (e.code !== 'EEXIST') throw e;
        const metadata = this.lockMetadata();
        if (metadata?.host === os.hostname() && nonempty(metadata.token) && Number.isSafeInteger(metadata.pid) && metadata.pid > 0 && Date.now()-Date.parse(metadata.created_at)>300000) {
          let absent = false; try { process.kill(metadata.pid,0); } catch (error) { absent = error.code === 'ESRCH'; }
          if (absent) { this.removeLock(metadata.token); continue; }
        }
        if (performance.now() >= deadline) throw new PapercutsError('lock_timeout',`Timed out waiting for journal lock: ${this.lockPath}`,{retryable:true});
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,25+Math.random()*75);
      }
    }
    try { writeFile(path.join(this.lockPath,'owner.json'),stableJSON({token,pid:process.pid,host:os.hostname(),created_at:new Date().toISOString()})+'\n'); }
    catch (e) { try { fs.rmdirSync(this.lockPath); } catch {} throw e; }
    return token;
  }
  mutation(callback, {allowTail = false} = {}) {
    this.check(true); this.parentIdentity = fs.lstatSync(this.directory);
    let token;
    try {
      token = this.acquireLock(); const data = this.bytes(); const {events,tail} = this.parse(data);
      if (tail && !allowTail) throw new PapercutsError('malformed_journal',`Journal has an incomplete final record: ${this.path}`,{suggested_fix:'Run doctor --repair-tail before mutating the journal.'});
      foldEvents(events,this.path);
      return callback(events,data,tail);
    } finally { try { if (token) this.removeLock(token); } finally { this.parentIdentity = null; } }
  }
  appendEventsLocked(events) {
    if (!events.length) return;
    const data = serializeEvents(events); this.check(true);
    const fd = regular(this.path,C.O_WRONLY|C.O_APPEND,{create:true});
    try { fs.writeFileSync(fd,data); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    syncDirectory(this.directory);
  }
  doctor({repair_tail = false} = {}) {
    const inspect = (events,data,tail) => {
      foldEvents(events,this.path); let repaired = false;
      if (tail && repair_tail) {
        this.check(); const fd = regular(this.path,C.O_WRONLY);
        try { fs.ftruncateSync(fd,data.lastIndexOf(10)+1); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
        data = data.subarray(0,data.lastIndexOf(10)+1); tail = false; repaired = true;
      }
      return {healthy:!tail,repaired,incomplete_tail:tail,byte_count:data.length,event_count:events.length};
    };
    if (repair_tail) return this.mutation(inspect,{allowTail:true});
    const data = this.bytes(), {events,tail} = this.parse(data); return inspect(events,data,tail);
  }
  replaceLocked(events,timestamp) {
    const replacement = serializeEvents(events), original = this.bytes();
    const backups = path.join(this.directory,'papercuts.backups');
    this.check(); privateDirectory(backups,true);
    const backup = path.join(backups,`papercuts-${timestamp.toISOString().replace(/[-:]/g,'')}-${crypto.randomUUID()}.jsonl`);
    writeFile(backup,original); syncDirectory(backups);
    const temporary = path.join(this.directory,`.papercuts-${crypto.randomUUID()}.tmp`);
    try {
      this.check(); writeFile(temporary,replacement); this.check();
      // Refuse a journal replaced by a link while the lock was held.
      const fd = regular(this.path,C.O_RDONLY,{missing:true}); if (fd !== null) fs.closeSync(fd);
      fs.renameSync(temporary,this.path); syncDirectory(this.directory);
    } finally { try { fs.unlinkSync(temporary); } catch (e) { if (e.code !== 'ENOENT') throw e; } }
    return {backup,before_bytes:original.length,after_bytes:replacement.length};
  }
}
