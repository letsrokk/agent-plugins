import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import readline from 'node:readline';
import {fileURLToPath} from 'node:url';
const root = fileURLToPath(new URL('../',import.meta.url));

async function connection(t,client) {
  const temporary = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'papercuts-offline-')));
  t.after(() => fs.rmSync(temporary,{recursive:true,force:true}));
  const installation = path.join(temporary,'plugin with spaces'),home = path.join(temporary,'home'),project = path.join(temporary,'project');
  fs.mkdirSync(installation); fs.mkdirSync(home,{mode:0o700}); fs.mkdirSync(project);
  for (const name of ['dist','package.json','plugin.json']) fs.cpSync(path.join(root,name),path.join(installation,name),{recursive:true});
  assert.ok(!fs.existsSync(path.join(installation,'node_modules')));
  // No Python, npm, Git, or downloader is available to the packaged process.
  const child = spawn(process.execPath,[path.join(installation,'dist/mcp_server.js')],{cwd:project,env:{HOME:home,PATH:installation,PAPERCUTS_CLIENT:client},stdio:['pipe','pipe','pipe']});
  const pending = new Map(); let seq = 0,stderr = '';
  const closed = new Promise(resolve => child.once('close',resolve));
  t.after(async () => { child.stdin.end(); const timer = setTimeout(() => child.kill(),1000); await closed; clearTimeout(timer); });
  child.stderr.on('data',chunk => {stderr+=chunk;});
  child.on('error',error => {for (const waiter of pending.values()) waiter.reject(error); pending.clear();});
  child.on('exit',code => {for (const waiter of pending.values()) waiter.reject(new Error(`MCP exited ${code}: ${stderr}`)); pending.clear();});
  readline.createInterface({input:child.stdout}).on('line',line => {
    const message = JSON.parse(line),waiter = pending.get(message.id);
    if (waiter) {pending.delete(message.id);clearTimeout(waiter.timer);waiter.resolve(message);}
  });
  const request = (method,params = {}) => new Promise((resolve,reject) => {
    const id = ++seq;
    const timer = setTimeout(() => {pending.delete(id);reject(new Error(`Timeout for ${method}: ${stderr}`));},10000);
    pending.set(id,{resolve,reject,timer}); child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');
  });
  const initialized = await request('initialize',{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'offline-test',version:'1'}});
  assert.equal(initialized.result.serverInfo.name,'papercuts');
  assert.equal(initialized.result.serverInfo.version,JSON.parse(fs.readFileSync(path.join(root,'plugin.json'),'utf8')).version);
  child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
  const call = async (name,args = {}) => {
    const message = await request('tools/call',{name,arguments:{project_root:project,...args}});
    assert.ok(!message.error,JSON.stringify(message));
    const text = JSON.parse(message.result.content[0].text);
    assert.deepEqual(text,message.result.structuredContent);
    return text;
  };
  return {request,call,home,project,stderr:() => stderr};
}
for (const client of ['codex','claude']) test(`offline bundled MCP ${client} initialization, tools, evidence and lifecycle`,async t => {
  const connection_ = await connection(t,client), {request,call,home} = connection_;
  const listing = await request('tools/list'); const tools = listing.result.tools;
  assert.deepEqual(tools.map(tool => tool.name).sort(),['apply_prune','get_complaint','inspect_storage','list_complaints','lodge_complaint','preview_prune','reopen_complaint','resolve_complaint','vote_for_complaint']);
  for (const tool of tools) assert.ok(tool.inputSchema.required.includes('project_root'));
  assert.equal(tools.find(tool => tool.name === 'apply_prune').annotations.destructiveHint,true);
  const inspect = await call('inspect_storage'); assert.equal(inspect.storage.path,path.join(home,`.${client}`,'papercuts.jsonl'));
  assert.ok(!fs.existsSync(path.dirname(inspect.storage.path)));
  const lodged = await call('lodge_complaint',{text:'Offline friction',evidence:'Observed during local test',severity:'major',tags:['tools']});
  assert.equal(lodged.changed,true); assert.equal(lodged.complaint.encounter_count,1); assert.ok(!('context' in lodged.complaint));
  const id = lodged.complaint.id;
  assert.equal((await call('vote_for_complaint',{complaint_id:id,note:'Repeated'})).complaint.encounter_count,2);
  assert.equal((await call('list_complaints',{limit:5})).count,1);
  const detail = await call('get_complaint',{complaint_id:id}); assert.equal(detail.complaint.context.note,'Observed during local test'); assert.equal(detail.complaint.agent,client);
  assert.equal((await call('resolve_complaint',{complaint_id:id,note:'Verified fix'})).complaint.status,'resolved');
  assert.equal((await call('reopen_complaint',{complaint_id:id,note:'Verified recurrence'})).complaint.status,'open');
  assert.equal((await call('resolve_complaint',{complaint_id:id})).changed,true);
  const preview = await call('preview_prune',{resolved_older_than_days:0});
  assert.equal(preview.preview.candidates.length,1);
  const applied = await call('apply_prune',{plan_id:preview.preview.plan_id,resolved_older_than_days:0});
  assert.equal(applied.result.removed_complaints,1); assert.ok(fs.existsSync(applied.result.backup));
  assert.equal((await call('list_complaints',{status:'all'})).count,0);
  assert.equal((await call('get_complaint',{complaint_id:'missing'})).error.code,'not_found');
  assert.equal((await call('inspect_storage',{project_root:'relative'})).error.code,'invalid_input');
  assert.equal(connection_.stderr(),'');
});
