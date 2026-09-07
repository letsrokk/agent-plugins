import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolveStorage,resolveClient,projectRef,discoverProject} from '../src/paths.js';
import {PapercutsService} from '../src/service.js';
import {JournalStore,foldEvents} from '../src/store.js';
import {sanitizeContext,sanitizeString} from '../src/models.js';
import {main} from '../src/cli.js';
const plugin = fileURLToPath(new URL('../',import.meta.url));
const remote = 'git@github.com:letsrokk/agent-plugins.git';
function fixture(t) {
  const temporary = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'papercuts-')));
  t.after(() => fs.rmSync(temporary,{recursive:true,force:true}));
  const root = path.join(temporary,'project'),home = path.join(temporary,'home');
  fs.mkdirSync(root,{mode:0o700}); fs.mkdirSync(home,{mode:0o700});
  const storage = resolveStorage(root,{home,environ:{},project_root:root,remote_url:remote});
  const service = new PapercutsService(storage,{now:() => new Date('2025-01-01T00:00:00Z')});
  return {temporary,root,home,storage,service};
}
const errorCode = code => error => error.code === code;
function cli(f,args,environ = {}) {
  let stdout = '',stderr = '';
  const status = main(args,{cwd:f.root,home:f.home,environ,stdout:{write:s => {stdout+=s;}},stderr:{write:s => {stderr+=s;}}});
  return {status,stdout,stderr};
}
test('legacy identifiers, journal fields and complete lifecycle remain compatible',t => {
  const f = fixture(t), {service,storage} = f;
  assert.deepEqual(projectRef(f.root,remote),projectRef(f.root,'https://github.com/letsrokk/agent-plugins'));
  const first = service.lodge('Validator hides the invalid manifest path',{severity:'major',tags:['tooling','validator']});
  const id = first.record.id;
  assert.equal(storage.project.id,'prj_408370c8a7daa01e');
  assert.equal(id,'pc_80eef530dc081102');
  const event = JSON.parse(fs.readFileSync(storage.journal_path,'utf8').split('\n')[0]);
  assert.equal(event.contract,1); assert.equal(event.agent,'codex'); assert.equal(event.kind,'complaint');
  assert.equal(service.lodge('  Validator hides the invalid manifest path  ',{tags:['validator','tooling']}).record.vote_count,1);
  assert.equal(service.vote(id.slice(0,8),{note:'Observed again'}).record.encounter_count,3);
  assert.equal(service.resolve(id,{note:'Verified fix'}).record.status,'resolved');
  assert.equal(service.resolve(id).changed,false);
  assert.equal(service.vote(id,{note:'Verified recurrence'}).record.status,'open');
  assert.equal(service.reopen(id).changed,false);
  assert.equal(service.get(id).vote_count,3);
  assert.equal(service.list({query:'MANIFEST',tags:['tooling']})[0].id,id);
  assert.equal(service.doctor().event_count,6);
  assert.equal(fs.statSync(storage.journal_path).mode & 0o777,0o600);
});
test('clients and projects stay isolated in private per-user journals',t => {
  const f = fixture(t); const id = f.service.lodge('Friction').record.id;
  const otherRoot = path.join(f.temporary,'other'); fs.mkdirSync(otherRoot);
  const other = new PapercutsService(resolveStorage(otherRoot,{home:f.home,environ:{},project_root:otherRoot,remote_url:'https://github.com/acme/other'}));
  assert.equal(other.list().length,0); assert.equal(other.list({all_projects:true})[0].id,id);
  assert.throws(() => other.vote(id),errorCode('not_found'));
  const claude = new PapercutsService(resolveStorage(f.root,{client:'claude',home:f.home,environ:{},project_root:f.root,remote_url:remote}));
  assert.equal(claude.list().length,0); assert.equal(claude.lodge('Friction').record.id,id);
  assert.equal(claude.get(id).agent,'claude'); assert.notEqual(claude.storage.journal_path,f.storage.journal_path);
  assert.equal(resolveClient(undefined,{}),'codex'); assert.equal(resolveClient('codex',{PAPERCUTS_CLIENT:'claude'}),'codex');
});
test('removed storage overrides fail explicitly without changing existing journals',t => {
  const f = fixture(t); f.service.lodge('Sentinel'); const before = fs.readFileSync(f.storage.journal_path);
  for (const args of [['--file','elsewhere','list'],['--file=elsewhere','list'],['config','set-scope','project','--level','project']]) assert.equal(cli(f,args).status,78);
  assert.equal(cli(f,['list'],{PAPERCUTS_FILE:'elsewhere'}).status,78);
  assert.equal(cli(f,['list'],{PAPERCUTS_FILE:''}).status,78);
  const directory = path.join(f.root,'.codex'); fs.mkdirSync(directory);
  const config = path.join(directory,'papercuts.config.json'); fs.writeFileSync(config,'{"scope":"project"}');
  assert.equal(cli(f,['list']).status,78); assert.equal(fs.readFileSync(config,'utf8'),'{"scope":"project"}');
  fs.writeFileSync(config,'{"scope":"user"}'); assert.equal(cli(f,['list']).status,0);
  fs.writeFileSync(path.join(f.home,'.codex/papercuts.config.json'),'{"scope":"project"}');
  assert.equal(cli(f,['list']).status,78);
  assert.deepEqual(fs.readFileSync(f.storage.journal_path),before);
});
test('CLI preserves JSON envelopes, markdown, evidence, argument failures and client selection',t => {
  const f = fixture(t);
  const evidence = path.join(f.root,'stderr.txt'); fs.writeFileSync(evidence,'Failed safely');
  const lodged = cli(f,['lodge','Useful friction','--severity','major','--tag','tools','--stderr-file','stderr.txt','--exit','2']);
  assert.equal(lodged.status,0,lodged.stderr); const payload = JSON.parse(lodged.stdout); assert.equal(payload.meta.contract,1);
  assert.equal(payload.data.record.context.stderr,'Failed safely'); assert.equal(payload.data.record.context.exit_status,2);
  assert.match(cli(f,['list','--format','md']).stdout,/^# Papercuts\n- pc_/);
  assert.equal(cli(f,['get','missing']).status,66); assert.equal(cli(f,['get','']).status,65);
  for (const args of [['list','--limit','NaN'],['list','--format','bad'],['list','--tag'],['list','extra'],['config','set'],['prune'],['--client','bad','list'],['list','--unknown']]) assert.equal(cli(f,args).status,2,args.join(' '));
  assert.equal(cli(f,['list'],{PAPERCUTS_CLIENT:'bad'}).status,78);
  const selected = cli(f,['--client','claude','config','show'],{PAPERCUTS_CLIENT:'codex'});
  assert.equal(selected.status,0,selected.stderr); assert.equal(JSON.parse(selected.stdout).data.path,path.join(f.home,'.claude/papercuts.jsonl'));
});
test('secret redaction retains actionable commands and bounds evidence before writes',t => {
  const f = fixture(t); f.service.lodge('Sentinel'); const before = fs.readFileSync(f.storage.journal_path);
  const secrets = sanitizeContext({command:"curl -H 'Authorization: Bearer bearer-secret' https://user:password@example.invalid API_TOKEN=token-value",stderr:'ghp_abcdefghijklmnopqrstuvwxyz123456 sk-proj-abcdefghijklmnopqrstuvwxyz123456',note:'AWS_ACCESS_KEY_ID=secret CI_JOB_JWT=jwt-secret'});
  for (const text of ['bearer-secret','user:password','token-value','ghp_','sk-proj-','jwt-secret']) assert.ok(!JSON.stringify(secrets).includes(text));
  for (const context of [{stderr:'HOME=/Users/example\nPATH=/bin'},{stderr:'Environment:\nAWS_ACCESS_KEY_ID=secret\nCI_JOB_JWT=secret'},{stderr:'HOME=a\0PATH=b\0'},{stderr:'{"AWS_ACCESS_KEY_ID":"a","CI_JOB_JWT":"b"}'},{env:{}},{command:'x'.repeat(1025)},{note:'x'.repeat(2049)},{stderr:'ü'.repeat(2049)},{exit_status:true},{stderr:'x',stderr_file:'x'}]) for (const dry_run of [false,true]) assert.throws(() => f.service.lodge('Invalid evidence',{context,dry_run}),errorCode('invalid_input'));
  assert.deepEqual(fs.readFileSync(f.storage.journal_path),before);
  for (const text of [String.raw`Prevention: native paths (C:\... or C:/...) while shell utilities take /c/... MSYS paths.`,String.raw`awk '/^\x60\x60\x60markdown$/{f=1;next} f&&/^\x60\x60\x60$/{exit} f' "5 Meta/Agent Instructions/Coding Agent Instructions.md" > mirror.md && diff mirror.md ~/.claude/CLAUDE.md`,"grep '/^foo$/' file","grep '/./' file","grep '/.*foo/' file","grep '/[ab]/i' file","sed -n '/^foo$/p' file",'./scripts/repro.sh','../src/models.py','.claude/skills/vault-task/SKILL.md:235-236 reads evidence']) assert.equal(sanitizeString(text),text);
  assert.equal(sanitizeString(String.raw`run /Users/alice/private/config then C:\Users\alice\secret.txt, open https://example.com/private). and clone git@github:acme/private.git`),'run [REDACTED_PATH] then [REDACTED_PATH], open [REDACTED_URL]). and clone [REDACTED_URL]');
  for (const [text,expected] of [['/^alice/private/key.txt','[REDACTED_PATH]'],['/[alice]/private/key.txt','[REDACTED_PATH]'],['/Users/alice/...','[REDACTED_PATH]']]) assert.equal(sanitizeString(text),expected);
  const a = f.service.lodge('Secret sk-proj-abcdefghijklmnopqrstuvwxyz123456',{tags:['sk-proj-abcdefghijklmnopqrstuvwxyz123456']});
  const b = f.service.lodge('Secret sk-proj-zyxwvutsrqponmlkjihgfedcba654321',{tags:['sk-proj-zyxwvutsrqponmlkjihgfedcba654321']});
  assert.equal(a.record.id,b.record.id);
});
test('evidence files reject links, non-UTF8 and oversize data',t => {
  const f = fixture(t),file = path.join(f.root,'evidence'); fs.writeFileSync(file,'valid');
  assert.equal(sanitizeContext({stderr_file:file}).stderr,'valid');
  fs.symlinkSync(file,file+'.link'); assert.throws(() => sanitizeContext({stderr_file:file+'.link'}),errorCode('invalid_input'));
  fs.writeFileSync(file,Buffer.from([255])); assert.throws(() => sanitizeContext({stderr_file:file}),errorCode('invalid_input'));
  fs.writeFileSync(file,Buffer.alloc(1048577)); assert.throws(() => sanitizeContext({stderr_file:file}),errorCode('invalid_input'));
});
test('unsafe journal directories, links, hard links and nonregular files are refused',t => {
  const f = fixture(t); f.service.lodge('Sentinel');
  const journal = f.storage.journal_path, directory = path.dirname(journal), outside = path.join(f.root,'outside');
  fs.writeFileSync(outside,'sentinel',{mode:0o600}); fs.unlinkSync(journal); fs.symlinkSync(outside,journal);
  assert.throws(() => f.service.list(),errorCode('invalid_input')); assert.throws(() => f.service.lodge('No'),errorCode('invalid_input')); assert.equal(fs.readFileSync(outside,'utf8'),'sentinel');
  fs.unlinkSync(journal); fs.linkSync(outside,journal); assert.throws(() => f.service.list(),errorCode('invalid_input')); fs.unlinkSync(journal);
  fs.mkdirSync(journal); assert.throws(() => f.service.list(),errorCode('invalid_input')); fs.rmdirSync(journal);
  fs.chmodSync(directory,0o777); assert.throws(() => f.service.list(),errorCode('invalid_input')); fs.chmodSync(directory,0o700);
  fs.rmdirSync(directory); fs.symlinkSync(f.root,directory); assert.throws(() => f.service.list(),errorCode('invalid_input'));
  assert.throws(() => new JournalStore({...f.storage,journal_path:outside}),errorCode('invalid_input'));
});
test('journal folding rejects malformed interiors and relational corruption; tail repair is explicit',t => {
  const f = fixture(t); const event = f.service.lodge('Sentinel').record; const journal = f.storage.journal_path;
  const valid = JSON.parse(fs.readFileSync(journal,'utf8'));
  const write = events => fs.writeFileSync(journal,events.map(e => JSON.stringify(e)+'\n').join(''));
  for (const events of [[{...valid,kind:[]}],[{...valid,severity:[]}],[valid,valid],[{...valid,kind:'encounter',complaint_id:'missing',note:null}],[valid,{...valid,kind:'encounter',complaint_id:valid.id,project:{...valid.project,id:'other'},note:null}]]) {
    write(events); assert.throws(() => f.service.doctor(),errorCode('malformed_journal')); assert.throws(() => f.service.lodge('Blocked'),errorCode('malformed_journal'));
  }
  write([valid]); fs.appendFileSync(journal,'{"incomplete":');
  assert.equal(f.service.list()[0].id,event.id); assert.equal(f.service.doctor().incomplete_tail,true);
  assert.throws(() => f.service.vote(event.id),errorCode('malformed_journal'));
  assert.equal(f.service.doctor({repair_tail:true}).repaired,true); assert.equal(f.service.doctor().healthy,true);
  fs.appendFileSync(journal,'invalid\n'); assert.throws(() => f.service.doctor({repair_tail:true}),errorCode('malformed_journal'));
});
test('stale prune plans never change data and fresh pruning preserves exact backups',t => {
  const f = fixture(t),old = f.service.lodge('Old friction').record.id;
  const service = new PapercutsService(f.storage,{now:() => new Date('2026-09-01T00:00:00Z')});
  const preview = service.previewPrune(); assert.deepEqual(preview.candidates.map(c => c.id),[old]);
  assert.ok(!fs.existsSync(path.join(path.dirname(f.storage.journal_path),'papercuts.backups')));
  service.lodge('New friction'); const before = fs.readFileSync(f.storage.journal_path);
  assert.throws(() => service.applyPrune({},preview.plan_id),errorCode('stale_prune_plan')); assert.deepEqual(fs.readFileSync(f.storage.journal_path),before);
  const fresh = service.previewPrune(), applied = service.applyPrune({},fresh.plan_id);
  assert.equal(applied.removed_complaints,1); assert.deepEqual(fs.readFileSync(applied.backup),before);
  assert.equal(applied.reclaimed_bytes,before.length-fs.readFileSync(f.storage.journal_path).length);
  assert.equal(service.list()[0].text,'New friction'); assert.throws(() => service.get(old),errorCode('not_found'));
  const empty = service.previewPrune(); assert.equal(service.applyPrune({},empty.plan_id).changed,false);
});
test('lock symlinks are not followed and stale locks are recovered only for absent owners',t => {
  const f = fixture(t); f.service.lodge('Sentinel'); const lock = f.storage.journal_path+'.lock';
  const foreign = path.join(f.root,'foreign'); fs.mkdirSync(foreign,{mode:0o700}); fs.writeFileSync(path.join(foreign,'owner.json'),'sentinel');
  fs.symlinkSync(foreign,lock); assert.throws(() => f.service.lodge('Blocked'),errorCode('invalid_input')); assert.equal(fs.readFileSync(path.join(foreign,'owner.json'),'utf8'),'sentinel'); fs.unlinkSync(lock);
  fs.mkdirSync(lock,{mode:0o700}); fs.writeFileSync(path.join(lock,'owner.json'),JSON.stringify({token:'stale',pid:2147483647,host:os.hostname(),created_at:'2020-01-01T00:00:00Z'}),{mode:0o600});
  assert.equal(f.service.lodge('Recovered').changed,true); assert.ok(!fs.existsSync(lock));
});
test('concurrent CLI writers serialize encounters without losing events',async t => {
  const f = fixture(t);
  await Promise.all(Array.from({length:6},() => new Promise((resolve,reject) => {
    const child = spawn(process.execPath,[path.join(plugin,'scripts/papercuts'),'lodge','Concurrent friction'],{cwd:f.root,env:{PATH:process.env.PATH,HOME:f.home},stdio:['ignore','pipe','pipe']});
    let stderr = ''; child.stderr.on('data',chunk => {stderr+=chunk;}); child.on('error',reject); child.on('exit',code => code === 0 ? resolve() : reject(new Error(stderr)));
  })));
  const actual = new PapercutsService(resolveStorage(f.root,{home:f.home,environ:{}}));
  assert.equal(actual.list()[0].encounter_count,6); assert.equal(actual.doctor().event_count,6);
});
test('stale lock recovery tolerates competing writers',async t => {
  const f = fixture(t); fs.mkdirSync(path.join(f.home,'.codex'),{mode:0o755});
  const lock = f.storage.journal_path+'.lock'; fs.mkdirSync(lock,{mode:0o700});
  fs.writeFileSync(path.join(lock,'owner.json'),JSON.stringify({token:'stale',pid:2147483647,host:os.hostname(),created_at:'2020-01-01T00:00:00Z'}),{mode:0o600});
  await Promise.all(Array.from({length:8},() => new Promise((resolve,reject) => {
    const child = spawn(process.execPath,[path.join(plugin,'scripts/papercuts'),'lodge','Stale recovery contention'],{cwd:f.root,env:{PATH:process.env.PATH,HOME:f.home},stdio:['ignore','pipe','pipe']});
    let stderr = ''; child.stderr.on('data',chunk => {stderr+=chunk;}); child.on('error',reject); child.on('exit',code => code === 0 ? resolve() : reject(new Error(stderr)));
  })));
  const actual = new PapercutsService(resolveStorage(f.root,{home:f.home,environ:{}}));
  assert.equal(actual.list()[0].encounter_count,8); assert.ok(!fs.existsSync(lock));
});
test('Unicode query folding and tag ordering preserve Python-era matching and IDs',t => {
  const f = fixture(t);
  const record = f.service.lodge('Unicode tags',{tags:['😀','\ue000']}).record;
  assert.equal(record.id,'pc_b70c0743c1dd9ba7');
  assert.deepEqual(record.tags,['\ue000','😀']);
  f.service.lodge('Straße Σςσ');
  assert.equal(f.service.list({query:'STRASSE σσσ'}).length,1);
});
test('system paths stay readable while identifying descendants and quoted paths are elided',() => {
  const unchanged = ['bash /tmp and python /tmp differ','2>/dev/null suppresses stderr','/usr/bin/bash: unexpected EOF','`/tmp/...`.',String.raw`C:\tmp is a live directory`,
    ...['/','/tmp','/var/tmp','/dev','/usr','/usr/bin','/usr/local/bin','/etc','/bin','/dev/null','/dev/zero','/dev/random','/dev/urandom','/dev/tty','/bin/sh','/bin/bash','/usr/bin/sh','/usr/bin/bash','C:\\','C:/','/c/','c:/TMP','/c/Windows']];
  const cases = [...unchanged.map(text => [text,text]),
    ['/tmp/client-project/secret-file','/tmp/...'],['/usr/bin/customer-tool','/usr/bin/...'],['/usr/bin/bash/private','/usr/bin/...'],
    [String.raw`C:\Windows\Temp\customer-file`,String.raw`C:\Windows\...`],['c:/tmp/customer','c:/tmp/...'],['/c/Windows/customer','/c/Windows/...'],
    ['/home/alice/work/client','[REDACTED_PATH]'],['/work/customer-name/file','[REDACTED_PATH]'],['/tmp-other/client','[REDACTED_PATH]'],
    [String.raw`\\internal-host\share\file`,'[REDACTED_PATH]'],['/Users/alice/...','[REDACTED_PATH]'],
    ['`/tmp/private file` and "/home/alice/private file"', '`/tmp/...` and "[REDACTED_PATH]"'],
    [String.raw`'C:\Users\alice\Private Folder\file'`,"'[REDACTED_PATH]'"],
    [String.raw`"C:\tmp\Private Folder\file"`,String.raw`"C:\tmp\..."`],
    ['`https://example.invalid/private`.', '`[REDACTED_URL]`.'],['(`/tmp/client`).','(`/tmp/...`).'],
    ['API_TOKEN=/tmp/secret','API_TOKEN=[REDACTED]']];
  for (const [input,expected] of cases) {
    assert.equal(sanitizeString(input),expected,input);
    assert.equal(sanitizeString(expected),expected,`Repeated: ${input}`);
  }
});
test('lodge previews normalize the proposed payload without reading or changing the journal',t => {
  const f = fixture(t),directory = path.dirname(f.storage.journal_path);
  const text = '  Failure in /tmp/client  ',options = {severity:'major',tags:[' Tools ','tools'],context:{command:'bash /tmp/client',note:'API_TOKEN=private',stderr:'2>/dev/null',exit_status:2}};
  const preview = f.service.lodge(text,{...options,dry_run:true});
  assert.equal(preview.dry_run,true); assert.equal(preview.changed,false);
  assert.equal(preview.preview.text,'Failure in /tmp/...');
  assert.deepEqual(preview.preview.context,{command:'bash /tmp/...',note:'API_TOKEN=[REDACTED]',stderr:'2>/dev/null',exit_status:2});
  assert.ok(!fs.existsSync(directory));
  assert.throws(() => f.service.lodge(text,{dry_run:'true'}),errorCode('invalid_input'));
  const record = f.service.lodge(text,options).record;
  assert.deepEqual(preview.preview,Object.fromEntries(Object.keys(preview.preview).map(key => [key,record[key]])));
  f.service.resolve(record.id);
  const before = fs.readFileSync(f.storage.journal_path),entries = fs.readdirSync(directory);
  assert.deepEqual(f.service.lodge(text,{...options,dry_run:true}),preview);
  assert.deepEqual(fs.readFileSync(f.storage.journal_path),before); assert.deepEqual(fs.readdirSync(directory),entries);
  assert.equal(f.service.get(record.id).status,'resolved'); assert.equal(f.service.get(record.id).encounter_count,1);
  fs.writeFileSync(f.storage.journal_path,'invalid journal\n');
  assert.deepEqual(f.service.lodge(text,{...options,dry_run:true}),preview);
});
test('CLI dry-run exposes sanitized evidence and leaves missing storage untouched',t => {
  const f = fixture(t),file = path.join(f.root,'stderr.txt'); fs.writeFileSync(file,'Failed in /tmp/client');
  const args = ['lodge','Failure in /tmp/client','--severity','major','--tag','Tools','--cmd','bash /tmp/client','--exit','2','--stderr-file','stderr.txt','--evidence','API_TOKEN=private'];
  const preview = cli(f,[...args,'--dry-run']); assert.equal(preview.status,0,preview.stderr);
  const data = JSON.parse(preview.stdout).data;
  assert.equal(data.dry_run,true); assert.equal(data.changed,false); assert.equal(data.preview.context.stderr,'Failed in /tmp/...');
  assert.ok(!fs.existsSync(path.dirname(f.storage.journal_path)));
  const record = JSON.parse(cli(f,args).stdout).data.record;
  assert.deepEqual(data.preview,Object.fromEntries(Object.keys(data.preview).map(key => [key,record[key]])));
  assert.match(cli(f,['--help']).stdout,/--dry-run/);
});
