import {JournalStore, foldEvents, serializeEvents} from './store.js';
import {hash, stableJSON, sanitizeString, sanitizeContext, invalid, PapercutsError, nonempty, compareUnicode, casefold} from './models.js';

const normalizeText = value => { const text = sanitizeString(value,'complaint text').replace(/\s+/gu,' ').trim(); if (!text) throw invalid('complaint text must not be empty'); return text; };
function normalizeTags(tags = []) {
  if (!Array.isArray(tags)) throw invalid('tags must be a sequence of strings');
  const result = [...new Set(tags.map(tag => sanitizeString(tag,'tag').trim().toLowerCase()).filter(Boolean))].sort(compareUnicode);
  if (result.length > 10) throw invalid('at most ten tags are allowed'); return result;
}
function severity(value) { if (!['minor','major','blocker'].includes(value)) throw invalid('severity must be minor, major, or blocker'); }
function note(value) { return value == null ? null : sanitizeContext({note:value}).note; }
function date(value) {
  if (typeof value !== 'string' || !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) || !Number.isFinite(Date.parse(value))) throw new PapercutsError('malformed_journal',`Invalid journal timestamp: ${value}`);
  return Date.parse(value);
}
function timestamp(value) {
  if (!(value instanceof Date) || !Number.isFinite(value.getTime())) throw invalid('clock must return a valid Date');
  return value.toISOString().replace('.000Z','Z');
}
export function prunePolicy(input = {}) {
  const result = {resolved_older_than_days:30,open_max_encounters:1,open_inactive_for_days:90,projects:'current',...input};
  for (const key of ['resolved_older_than_days','open_max_encounters','open_inactive_for_days']) if (!Number.isSafeInteger(result[key]) || result[key] < 0) throw invalid('prune thresholds and encounter counts must be non-negative integers');
  if (!['current','all'].includes(result.projects) || Object.keys(result).length !== 4) throw invalid('Invalid pruning policy');
  return result;
}
export class PapercutsService {
  constructor(storage, {agent = storage.client, now = () => new Date()} = {}) { Object.assign(this,{storage,agent,now}); this.store = new JournalStore(storage); }
  event(kind,fields) { return {contract:1,kind,...fields,ts:timestamp(this.now()),agent:this.agent,project:this.storage.project}; }
  visible(records,all_projects) { return [...records].filter(record => all_projects || record.project.id === this.storage.project.id); }
  resolveId(records,id,all_projects = false) {
    if (!nonempty(id)) throw invalid('complaint ID must not be empty');
    const matches = this.visible(records,all_projects).filter(record => record.id.startsWith(id));
    if (!matches.length) throw new PapercutsError('not_found',`Complaint not found: ${id}`);
    if (matches.length > 1) throw new PapercutsError('ambiguous_id',`Complaint ID prefix is ambiguous: ${id}`);
    return matches[0];
  }
  lodge(text,{severity:level = 'minor',tags = [],context = {}} = {}) {
    text = normalizeText(text); tags = normalizeTags(tags); severity(level); context = sanitizeContext(context);
    const id = `pc_${hash(stableJSON({contract:1,project_id:this.storage.project.id,text,tags})).slice(0,16)}`;
    return this.store.mutation(events => {
      const existing = foldEvents(events).get(id), added = [];
      if (!existing) added.push(this.event('complaint',{id,text,severity:level,tags,context}));
      else {
        if (existing.project.id !== this.storage.project.id || existing.text !== text || stableJSON(existing.tags) !== stableJSON(tags)) throw new PapercutsError('internal_failure','Complaint ID collision detected; no event was appended.');
        if (existing.status === 'resolved') added.push(this.event('reopened',{complaint_id:id}));
        added.push(this.event('encounter',{complaint_id:id,note:null,context}));
      }
      this.store.appendEventsLocked(added); return {changed:true,record:foldEvents([...events,...added]).get(id)};
    });
  }
  list({status = 'open',query = null,tags = [],severity:level = null,min_encounters = null,recent_days = null,all_projects = false,limit = 50} = {}) {
    if (!['open','resolved','all'].includes(status)) throw invalid('status must be open, resolved, or all');
    if (level !== null) severity(level);
    for (const [key,value] of Object.entries({min_encounters,recent_days,limit})) if (value !== null && (!Number.isSafeInteger(value) || value < 0)) throw invalid(`${key} must be a non-negative integer`);
    tags = normalizeTags(tags); query = query ? casefold(normalizeText(query)) : null;
    const cutoff = recent_days === null ? null : this.now().getTime()-recent_days*86400000;
    const order = {blocker:0,major:1,minor:2};
    return this.visible(foldEvents(this.store.readEvents()).values(),all_projects)
      .filter(r => (status === 'all' || r.status === status) && (level === null || r.severity === level) && (min_encounters === null || r.encounter_count >= min_encounters) && tags.every(t => r.tags.includes(t)) && (query === null || casefold(r.text).includes(query)) && (cutoff === null || date(r.last_encounter_at) >= cutoff))
      .sort((a,b) => order[a.severity]-order[b.severity] || b.encounter_count-a.encounter_count || date(b.last_encounter_at)-date(a.last_encounter_at) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).slice(0,limit);
  }
  get(id,{all_projects = false} = {}) { return this.resolveId(foldEvents(this.store.readEvents()).values(),id,all_projects); }
  vote(id,{note:inputNote = null,context = {}} = {}) {
    const sanitizedNote = note(inputNote), sanitizedContext = sanitizeContext(context);
    return this.store.mutation(events => {
      const record = this.resolveId(foldEvents(events).values(),id), added = [];
      if (record.status === 'resolved') added.push(this.event('reopened',{complaint_id:record.id,note:null}));
      added.push(this.event('encounter',{complaint_id:record.id,note:sanitizedNote,context:sanitizedContext}));
      this.store.appendEventsLocked(added); return {changed:true,record:foldEvents([...events,...added]).get(record.id)};
    });
  }
  changeStatus(id,kind,{note:inputNote = null} = {}) {
    const sanitizedNote = note(inputNote);
    return this.store.mutation(events => {
      const record = this.resolveId(foldEvents(events).values(),id);
      if (record.status === (kind === 'resolved' ? 'resolved' : 'open')) return {changed:false,record};
      const event = this.event(kind,{complaint_id:record.id,note:sanitizedNote});
      this.store.appendEventsLocked([event]); return {changed:true,record:foldEvents([...events,event]).get(record.id)};
    });
  }
  resolve(id,options) { return this.changeStatus(id,'resolved',options); }
  reopen(id,options) { return this.changeStatus(id,'reopened',options); }
  doctor(options) { return this.store.doctor(options); }
  inspectStorage() {
    const health = this.store.doctor();
    return {scope:'user',path:this.storage.journal_path,project:this.storage.project,byte_count:health.byte_count,event_count:health.event_count,healthy:health.healthy};
  }
  preview(events,digest,policy,moment) {
    timestamp(moment);
    const stats = new Map();
    for (const event of events) {
      const id = event.kind === 'complaint' ? event.id : event.complaint_id;
      const stat = stats.get(id) ?? {event_count:0,estimated_bytes:0};
      stat.event_count++; stat.estimated_bytes += serializeEvents([event]).length; stats.set(id,stat);
    }
    const candidates = [];
    for (const record of foldEvents(events).values()) {
      if (policy.projects === 'current' && record.project.id !== this.storage.project.id) continue;
      let reason;
      if (record.status === 'resolved') {
        const resolved = record.status_history.findLast(event => event.kind === 'resolved');
        if (!resolved) throw new PapercutsError('malformed_journal',`Resolved complaint lacks a resolution event: ${record.id}`);
        const cutoff = new Date(moment.getTime()-policy.resolved_older_than_days*86400000);
        if (date(resolved.ts) < cutoff.getTime()) reason = `resolved before ${timestamp(cutoff)}`;
      } else {
        const cutoff = new Date(moment.getTime()-policy.open_inactive_for_days*86400000);
        if (record.encounter_count <= policy.open_max_encounters && date(record.last_encounter_at) < cutoff.getTime()) reason = `open with at most ${policy.open_max_encounters} encounters and inactive since before ${timestamp(cutoff)}`;
      }
      if (reason) candidates.push({id:record.id,project:record.project,status:record.status,reason,...stats.get(record.id)});
    }
    candidates.sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    const plan_id = `pp_${hash(stableJSON({journal_digest:digest,policy,candidate_ids:candidates.map(c => c.id)})).slice(0,24)}`;
    return {plan_id,policy,candidates,estimated:{complaints:candidates.length,events:candidates.reduce((n,c) => n+c.event_count,0),bytes:candidates.reduce((n,c) => n+c.estimated_bytes,0)}};
  }
  previewPrune(input = {}) { const policy = prunePolicy(input), moment = this.now(), {events,digest} = this.store.snapshot(); return this.preview(events,digest,policy,moment); }
  applyPrune(input,plan_id) {
    const policy = prunePolicy(input); if (!nonempty(plan_id)) throw invalid('plan_id must not be empty'); const moment = this.now();
    return this.store.mutation((events,data) => {
      const preview = this.preview(events,hash(data),policy,moment);
      if (preview.plan_id !== plan_id) throw new PapercutsError('stale_prune_plan','The prune plan no longer matches the journal and policy.',{retryable:true,suggested_fix:'Preview pruning again before applying it.'});
      const ids = new Set(preview.candidates.map(c => c.id));
      if (!ids.size) return {changed:false,plan_id,policy,backup:null,removed_complaints:0,removed_events:0,reclaimed_bytes:0};
      const survivors = events.filter(e => !ids.has(e.kind === 'complaint' ? e.id : e.complaint_id));
      const {backup,before_bytes,after_bytes} = this.store.replaceLocked(survivors,moment);
      return {changed:true,plan_id,policy,backup,removed_complaints:ids.size,removed_events:events.length-survivors.length,reclaimed_bytes:before_bytes-after_bytes};
    });
  }
}
