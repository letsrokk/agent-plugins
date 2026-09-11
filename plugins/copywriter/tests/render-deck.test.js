const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { inflateRawSync } = require('node:zlib');
const { renderDeck, validate, processOutcome } = require('../vendor/deck.cjs');
function zipEntries(file) {
  const bytes = fs.readFileSync(file), entries = {};
  let end = bytes.length - 22;
  while (bytes.readUInt32LE(end) !== 0x06054b50) end--;
  let offset = bytes.readUInt32LE(end + 16);
  while (bytes.readUInt32LE(offset) === 0x02014b50) {
    const size = bytes.readUInt32LE(offset + 20), length = bytes.readUInt16LE(offset + 28), extra = bytes.readUInt16LE(offset + 30), comment = bytes.readUInt16LE(offset + 32), local = bytes.readUInt32LE(offset + 42);
    const name = bytes.toString('utf8', offset + 46, offset + 46 + length);
    const start = local + 30 + bytes.readUInt16LE(local + 26) + bytes.readUInt16LE(local + 28);
    const data = bytes.subarray(start, start + size);
    entries[name] = bytes.readUInt16LE(offset + 10) === 8 ? inflateRawSync(data) : data;
    offset += 46 + length + extra + comment;
  }
  return entries;
}
test('editable deck contains notes, chart data, images, and rejects escaping or invalid input', async t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'copywriter-deck-test-'));
  t.after(() => fs.rmSync(dir, {recursive:true,force:true}));
  const base = fs.mkdirSync(path.join(dir,'source')) || path.join(dir,'source');
  fs.writeFileSync(path.join(base,'pixel.png'),Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aE1sAAAAASUVORK5CYII=','base64'));
  fs.writeFileSync(path.join(base,'data.json'), JSON.stringify({units:'requests',labels:['A','B'],series:[{name:'Observed',values:[2,7]}],source:'Authored fixture',method:'Counted fixture requests'}));
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><title>Flow</title><rect x="5" y="5" width="80" height="30" fill="#ffffff"/><text x="10" y="20">A &amp; B</text></svg>';
  fs.writeFileSync(path.join(base,'diagram.svg'), svg);
  const slide=(id,layout,more={})=>({id,title:`${id}: Unicode café — Δ`,body:'A source-grounded point.',notes:`Evidence for ${id}.`,claim_ids:['C1'],asset_ids:[],layout,...more});
  const model={title:'Fixture',fontFace:'Missing-Font-Fixture',language:'fr-FR',claims:[{id:'C1'}],assets:[{id:'A1',file:'pixel.png',alt:'One pixel test image',source_file:'diagram.svg'}],slides:[slide('intro','title'),slide('data','chart',{chart:{file:'data.json',type:'bar',alt:'A has 2 requests; B has 7 requests.'}}),slide('image','image',{asset_ids:['A1']}),slide('columns','two-column',{columns:[{title:'One',body:'First point'},{title:'Two',body:'Second point'}]}),slide('diagram','diagram',{asset_ids:['A1']}),...['statement','closing','sources','appendix'].map(layout=>slide(layout,layout))]};
  const input=path.join(base,'input.json');
  fs.writeFileSync(input,JSON.stringify(model));
  const output=path.join(dir,'output');
  const status=await renderDeck(input,output,dir);
  assert.equal(status.pptx,'generated');
  assert.equal(fs.readFileSync(path.join(output,'diagram.svg'),'utf8'), svg);
  assert.equal(status.visual_review,'not checked');
  const entries=zipEntries(path.join(output,'pitch-deck.pptx'));
  assert.equal(Object.keys(entries).filter(n=>/^ppt\/slides\/slide\d+\.xml$/.test(n)).length,model.slides.length);
  assert.match(entries['ppt/slides/slide1.xml'].toString(),/café/);
  assert.match(entries['ppt/notesSlides/notesSlide1.xml'].toString(),/Evidence for intro/);
  assert.match(entries['ppt/charts/chart1.xml'].toString(),/<c:v>7<\/c:v>/);
  assert.ok(Object.keys(entries).some(n=>n.startsWith('ppt/embeddings/')&&n.endsWith('.xlsx')));
  assert.ok(Object.keys(entries).some(n=>/^ppt\/media\/.+\.png$/.test(n)));
  assert.match(entries['ppt/slides/slide3.xml'].toString(),/One pixel test image/);
  const picture = entries['ppt/slides/slide3.xml'].toString().match(/<p:pic>[\s\S]*?<\/p:pic>/)[0];
  const extent = picture.match(/<a:ext cx="(\d+)" cy="(\d+)"/);
  assert.equal(extent[1], extent[2], 'square source preserves its aspect ratio');
  assert.match(entries['ppt/slides/slide1.xml'].toString(), /fr-FR/);
  await assert.rejects(()=>renderDeck(input,path.resolve(__dirname,'../forbidden-output'),path.resolve(__dirname,'..')),/installed plugin/);
  await assert.rejects(()=>renderDeck(input,output,dir),/new directory/);
  model.assets[0].file='../private.png'; fs.writeFileSync(input,JSON.stringify(model));
  await assert.rejects(()=>renderDeck(input,path.join(dir,'bad'),dir),/relative file/);
  fs.copyFileSync(path.join(base,'pixel.png'),path.join(dir,'private.png'));
  fs.symlinkSync(path.join(dir,'private.png'),path.join(base,'escape.png'));
  model.assets[0].file='escape.png';fs.writeFileSync(input,JSON.stringify(model));
  await assert.rejects(()=>renderDeck(input,path.join(dir,'bad'),dir),/escapes/);
  model.assets[0].file='https://example.com/image.png';fs.writeFileSync(input,JSON.stringify(model));
  await assert.rejects(()=>renderDeck(input,path.join(dir,'bad'),dir),/relative file/);
  model.assets[0].file='pixel.png';model.slides[1].chart.file='missing.json';fs.writeFileSync(input,JSON.stringify(model));
  await assert.rejects(()=>renderDeck(input,path.join(dir,'bad'),dir),/ENOENT/);
  model.slides[1].chart.file='data.json';model.slides[0].claim_ids=['missing'];fs.writeFileSync(input,JSON.stringify(model));
  await assert.rejects(()=>renderDeck(input,path.join(dir,'bad'),dir),/Missing claim/);
  assert.equal(fs.existsSync(path.join(dir,'bad')),false);
  model.slides[0].claim_ids=['C1'];
  for (const unsafe of ['<script>alert(1)</script>', '<image href="https://example.com/pixel"/>', '<rect onclick="alert(1)"/>', '<rect fill="url(https://example.com/paint)"/>', '<rect fill="url&#40;https://example.com/paint)"/>', '<style>@import url(https://example.com)</style>']) {
    fs.writeFileSync(path.join(base,'diagram.svg'), '<svg>'+unsafe+'</svg>');
    assert.throws(()=>validate(model,fs.realpathSync(base)), /SVG/);
  }
});

test('render stage records unavailable tools, timeouts, nonzero exits and missing files separately', () => {
  assert.equal(processOutcome({error:{code:'ENOENT'},status:null},false,'pdftoppm').status,'unavailable');
  assert.equal(processOutcome({error:{code:'ETIMEDOUT'},status:null,signal:'SIGTERM'},false,'LibreOffice').status,'timed out');
  const failure=processOutcome({status:7,stderr:'Conversion refused'},false,'LibreOffice');
  assert.equal(failure.exit_status,7);
  assert.equal(failure.stderr,'Conversion refused');
  assert.match(failure.next_action,/retry/);
  assert.equal(processOutcome({status:0},false,'pdftoppm').status,'missing output');
  assert.equal(processOutcome({status:0},true,'pdftoppm').status,'generated');
});
