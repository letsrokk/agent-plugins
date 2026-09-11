'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {packagePlugin} = require('../scripts/package');

test('three relocated packages contain one manifest and runnable generators without npm', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'copywriter-package-'));
  t.after(() => fs.rmSync(root, {recursive:true, force:true}));
  const out = packagePlugin(path.join(root, 'releases'));
  for (const target of ['portable','codex','claude']) {
    const folder = path.join(out, `copywriter-${target}`, 'copywriter');
    assert.equal(['plugin.json','.codex-plugin/plugin.json','.claude-plugin/plugin.json'].filter(file => fs.existsSync(path.join(folder,file))).length, 1);
    assert(!fs.existsSync(path.join(folder,'node_modules')));
    assert(!fs.existsSync(path.join(folder,'tests')));
    const skills = fs.readdirSync(path.join(folder,'skills'));
    assert.equal(skills.length, 6);
    for (const skill of skills) {
      const file = path.join(folder,'skills',skill,'SKILL.md');
      for (const match of fs.readFileSync(file,'utf8').matchAll(/\[[^\]]*\]\(([^\s)]+)\)/g)) {
        if (/^[a-z]+:/i.test(match[1])) continue;
        const referenced = path.resolve(path.dirname(file),match[1].split('#')[0]);
        assert(referenced.startsWith(folder + path.sep));
        assert(fs.existsSync(referenced), `${skill}: ${match[1]}`);
      }
    }
    const result = spawnSync(process.execPath, [path.join(folder,'scripts/render-deck.js')], {cwd:root, encoding:'utf8'});
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Usage:/);
    assert(!result.stderr.includes('MODULE_NOT_FOUND'));
    const input = path.join(root, 'slides.json');
    fs.writeFileSync(input, JSON.stringify({title:'Fixture',claims:[],assets:[],slides:[{id:'intro',title:'Hello',body:'A local deck.',notes:'Source notes.',claim_ids:[],asset_ids:[],layout:'title'}]}));
    const output = path.join(root, `${target}-deck`);
    const generated = spawnSync(process.execPath, [path.join(folder,'scripts/render-deck.js'), input, output], {cwd:root, encoding:'utf8', env:{...process.env, PATH:''}});
    assert.equal(generated.status, 0, generated.stderr);
    assert(fs.existsSync(path.join(output,'pitch-deck.pptx')));
    assert.equal(JSON.parse(fs.readFileSync(path.join(output,'render-status.json'),'utf8')).previews, 'generated');
    assert(!fs.existsSync(path.join(output,'pitch-deck.pdf')));
    assert.deepEqual(fs.readdirSync(path.join(output,'previews')), ['slide-1.svg']);
  }
  assert.throws(() => packagePlugin(out), /EEXIST/);
});
