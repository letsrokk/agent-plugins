import path from 'node:path';
import {parseArgs} from 'node:util';
import {resolveClient,resolveStorage} from './paths.js';
import {PapercutsService} from './service.js';
import {PapercutsError,errorResult,stableJSON} from './models.js';

const strings = names => Object.fromEntries(names.map(name => [name,{type:'string'}]));
const booleans = names => Object.fromEntries(names.map(name => [name,{type:'boolean'}]));
const evidence = strings(['cmd','exit','stderr-file']);
const policies = strings(['resolved-older-than-days','open-max-encounters','open-inactive-for-days','projects']);
const optionsByCommand = {
  lodge:{...strings(['severity','evidence']),tag:{type:'string',multiple:true},...evidence},
  list:{...strings(['status','query','severity','min-encounters','recent-days','limit','format']),...booleans(['all-projects']),tag:{type:'string',multiple:true}},
  get:booleans(['all-projects']), vote:{...strings(['note']),...evidence},resolve:strings(['note']),reopen:strings(['note']),doctor:booleans(['repair-tail']),prune:policies,config:{}
};
function usage(message) { throw new PapercutsError('usage',message); }
export function main(argv = process.argv.slice(2),{cwd = process.cwd(),environ = process.env,home,stdout = process.stdout,stderr = process.stderr} = {}) {
  try {
    if (argv.includes('--help') || argv.includes('-h')) {
      stdout.write('Usage: papercuts [--client codex|claude] COMMAND\nCommands: lodge TEXT, list, get ID, vote ID, resolve ID, reopen ID, doctor, prune preview, prune apply PLAN_ID, config show\n' + Object.entries(optionsByCommand).map(([name,options]) => `${name}: ${Object.keys(options).map(key => `--${key}`).join(' ')}`).join('\n') + '\n');
      return 0;
    }
    if (argv.includes('--file') || argv.some(arg => arg.startsWith('--file=')) || (argv.includes('config') && argv.includes('set-scope'))) throw new PapercutsError('invalid_config','Custom journals and config set-scope are no longer supported; migrate old journals manually.');
    let clientArg;
    if (argv[0] === '--client') { clientArg = argv[1]; if (!clientArg) usage('--client requires a value'); argv = argv.slice(2); }
    else if (argv[0]?.startsWith('--client=')) { clientArg = argv[0].slice(9); argv = argv.slice(1); }
    const command = argv[0];
    if (!Object.hasOwn(optionsByCommand,command)) usage('Expected lodge, list, get, vote, resolve, reopen, doctor, prune, or config');
    let values,positionals;
    try { ({values,positionals} = parseArgs({args:argv.slice(1),options:optionsByCommand[command],allowPositionals:true,strict:true})); } catch (e) { usage(e.message); }
    const subcommand = ['config','prune'].includes(command) ? positionals.shift() : null;
    if (command === 'config' && subcommand !== 'show') usage('Expected config show');
    if (command === 'prune' && !['preview','apply'].includes(subcommand)) usage('Expected prune preview or prune apply');
    const expected = ['lodge','get','vote','resolve','reopen'].includes(command) || (command === 'prune' && subcommand === 'apply') ? 1 : 0;
    if (positionals.length !== expected) usage(`Expected ${expected} argument(s) for ${command}`);
    const opts = {};
    for (const [key,value] of Object.entries(values)) opts[key.replaceAll('-','_')] = value;
    for (const key of ['exit','min_encounters','recent_days','limit','resolved_older_than_days','open_max_encounters','open_inactive_for_days']) if (key in opts) {
      if (!/^[+-]?\d+$/.test(opts[key]) || !Number.isSafeInteger(Number(opts[key]))) usage(`${key} must be an integer`); opts[key] = Number(opts[key]);
    }
    if (opts.format && !['json','md'].includes(opts.format)) usage('format must be json or md');
    const client = resolveClient(clientArg,environ), storage = resolveStorage(cwd,{client,environ,...(home ? {home} : {})}), service = new PapercutsService(storage);
    const context = {};
    if ('cmd' in opts) context.command = opts.cmd;
    if ('exit' in opts) context.exit_status = opts.exit;
    if ('stderr_file' in opts) context.stderr_file = path.resolve(cwd,opts.stderr_file);
    if ('evidence' in opts) context.note = opts.evidence;
    let data;
    if (command === 'lodge') data = service.lodge(positionals[0],{...opts,tags:opts.tag ?? [],context});
    else if (command === 'list') data = service.list({...opts,tags:opts.tag ?? []});
    else if (command === 'get') data = service.get(positionals[0],opts);
    else if (command === 'vote') data = service.vote(positionals[0],{note:opts.note,context});
    else if (command === 'resolve' || command === 'reopen') data = service[command](positionals[0],opts);
    else if (command === 'doctor') data = service.doctor(opts);
    else if (command === 'config') data = service.inspectStorage();
    else data = subcommand === 'preview' ? service.previewPrune(opts) : service.applyPrune(opts,positionals[0]);
    if (command === 'list' && opts.format === 'md') stdout.write(['# Papercuts',...data.map(r => `- ${r.id} [${r.severity}] ${r.encounter_count} encounters — ${r.project.name}: ${r.text}`)].join('\n')+'\n');
    else stdout.write(stableJSON({ok:true,data,meta:{contract:1,file:storage.journal_path}})+'\n');
    return 0;
  } catch (e) {
    const result = errorResult(e); stderr.write(stableJSON({...result,meta:{contract:1}})+'\n');
    return {usage:2,invalid_input:65,malformed_journal:65,not_found:66,ambiguous_id:66,internal_failure:70,io_failure:74,stale_prune_plan:75,lock_timeout:75,permission_denied:77,invalid_config:78}[result.error.code] ?? 70;
  }
}
