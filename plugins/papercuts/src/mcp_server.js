import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {StdioServerTransport} from '@modelcontextprotocol/sdk/server/stdio.js';
import {z} from 'zod';
import {resolveClient,resolveStorage} from './paths.js';
import {PapercutsService} from './service.js';
import {errorResult,invalid} from './models.js';

const summary = r => Object.fromEntries(['id','text','status','severity','tags','project','encounter_count','last_encounter_at'].map(k => [k,r[k]]));
const context = args => Object.fromEntries(['command','exit_status','stderr'].filter(k => args[k] != null).map(k => [k,args[k]]));
const policy = args => ({resolved_older_than_days:args.resolved_older_than_days ?? 30,open_max_encounters:args.open_max_encounters ?? 1,open_inactive_for_days:args.open_inactive_for_days ?? 90,projects:args.all_projects ? 'all' : 'current'});
export function invokeTool(service,name,args) {
  try {
    if (name === 'list_complaints') { const records = service.list({...args,tags:args.tags ?? []}); return {complaints:records.map(summary),count:records.length}; }
    if (name === 'get_complaint') return {complaint:service.get(args.complaint_id,args)};
    if (name === 'inspect_storage') return {storage:service.inspectStorage()};
    if (name === 'preview_prune') return {preview:service.previewPrune(policy(args))};
    if (name === 'apply_prune') return {result:service.applyPrune(policy(args),args.plan_id)};
    let result;
    if (name === 'lodge_complaint') result = service.lodge(args.text,{severity:args.severity,tags:args.tags ?? [],context:{...context(args),...(args.evidence == null ? {} : {note:args.evidence})}});
    else if (name === 'vote_for_complaint') result = service.vote(args.complaint_id,{note:args.note,context:context(args)});
    else if (name === 'resolve_complaint') result = service.resolve(args.complaint_id,args);
    else if (name === 'reopen_complaint') result = service.reopen(args.complaint_id,args);
    else throw invalid(`unknown MCP tool: ${name}`);
    return {complaint:summary(result.record),changed:result.changed};
  } catch (error) { return errorResult(error); }
}
export function invokeProjectTool(name,args,{client = resolveClient(),home,environ = process.env} = {}) {
  try {
    if (typeof args.project_root !== 'string' || !path.isAbsolute(args.project_root) || !fs.statSync(args.project_root,{throwIfNoEntry:false})?.isDirectory()) throw invalid('project_root must be an existing absolute directory');
    const storage = resolveStorage(args.project_root,{client,environ,...(home ? {home} : {})});
    return invokeTool(new PapercutsService(storage),name,args);
  } catch (error) { return errorResult(error); }
}
const optionalString = () => z.string().nullable().optional();
const evidence = {command:optionalString(),exit_status:z.number().int().nullable().optional(),stderr:optionalString()};
const allProjects = {all_projects:z.boolean().default(false)};
const id = {complaint_id:z.string()};
const thresholds = {resolved_older_than_days:z.number().int().nonnegative().default(30),open_max_encounters:z.number().int().nonnegative().default(1),open_inactive_for_days:z.number().int().nonnegative().default(90),...allProjects};
const level = z.enum(['minor','major','blocker']);
const definitions = {
  lodge_complaint:['Lodge concise workflow friction when no existing open complaint matches.',{text:z.string(),severity:level.default('minor'),tags:z.array(z.string()).nullable().optional(),...evidence,evidence:optionalString()}],
  list_complaints:['Search complaints before lodging new friction or reviewing existing work.',{status:z.enum(['open','resolved','all']).default('open'),query:optionalString(),tags:z.array(z.string()).nullable().optional(),severity:level.nullable().optional(),min_encounters:z.number().int().nonnegative().nullable().optional(),recent_days:z.number().int().nonnegative().nullable().optional(),limit:z.number().int().nonnegative().default(50),...allProjects}],
  get_complaint:['Inspect one complaint by full ID or unique prefix before acting on it.',{...id,...allProjects}],
  vote_for_complaint:['Record another encounter when existing workflow friction clearly matches.',{...id,note:optionalString(),...evidence}],
  resolve_complaint:['Resolve a complaint when verified evidence shows the friction no longer occurs.',{...id,note:optionalString()}],
  reopen_complaint:['Reopen a complaint when verified evidence shows the friction returns.',{...id,note:optionalString()}],
  inspect_storage:['Inspect the active journal location and health without changing it.',{}],
  preview_prune:['Preview exact complaints a pruning policy would remove without applying it.',thresholds],
  apply_prune:['Apply the exact preview plan only after explicit user authorization.',{plan_id:z.string(),...thresholds}]
};
export function createServer({client = resolveClient()} = {}) {
  const manifest = JSON.parse(fs.readFileSync(new URL('../plugin.json',import.meta.url),'utf8'));
  const server = new McpServer({name:'papercuts',version:manifest.version},{instructions:'When material workflow friction occurs, search open complaints in the active project. Vote for a clear match; otherwise lodge a concise complaint. Never apply pruning without explicit user authorization for the preview plan.'});
  for (const [name,[description,properties]] of Object.entries(definitions)) {
    const readOnlyHint = ['list_complaints','get_complaint','inspect_storage','preview_prune'].includes(name);
    server.registerTool(name,{description,inputSchema:{project_root:z.string(),...properties},annotations:{readOnlyHint,openWorldHint:false,...(readOnlyHint ? {} : {destructiveHint:name === 'apply_prune',idempotentHint:false})}},async args => {
      const result = invokeProjectTool(name,args,{client});
      return {content:[{type:'text',text:JSON.stringify(result)}],structuredContent:result,...(result.ok === false ? {isError:true} : {})};
    });
  }
  return server;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (Number(process.versions.node.split('.')[0]) < 24) { console.error('Papercuts requires Node.js 24 or later on PATH.'); process.exitCode = 78; }
  else { try { await createServer().connect(new StdioServerTransport()); } catch (error) { console.error(JSON.stringify(errorResult(error))); process.exitCode = 78; } }
}
