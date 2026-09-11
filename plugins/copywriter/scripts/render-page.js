#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text = value => { assert.equal(typeof value, 'string', 'Expected text'); assert(value.trim(), 'Empty text'); return escape(value); };

function renderPage(input, destination, workspace = process.cwd()) {
  const source = fs.realpathSync(input);
  const root = path.dirname(source);
  const page = JSON.parse(fs.readFileSync(source, 'utf8'));
  const title = text(page.title), description = text(page.description);
  const audience = text(page.audience);
  const heading = text(page.hero.heading), body = text(page.hero.body);
  const label = text(page.cta.text);
  let cta = `<button type="button" disabled>${label}</button>`;
  if (page.cta.url) {
    const url = new URL(page.cta.url);
    assert(['https:', 'http:'].includes(url.protocol) && !url.username && !url.password, 'CTA must be a public HTTP(S) URL');
    cta = `<a class="cta" href="${escape(url.href)}">${label}</a>`;
  }
  assert(Array.isArray(page.sections) && page.sections.length, 'Sections required');
  const assets = [], ids = new Set();
  const sections = page.sections.map(section => {
    assert(/^[a-z][a-z0-9-]*$/.test(section.id) && !ids.has(section.id), 'Unique section IDs required');
    ids.add(section.id);
    let illustration = '';
    if (section.image) {
      const {file, alt, caption} = section.image;
      assert(typeof file === 'string' && !path.isAbsolute(file), 'Asset must be relative');
      const resolved = fs.realpathSync(path.resolve(root, file));
      assert(resolved.startsWith(root + path.sep), 'Asset escapes source directory');
      assert(/\.(png|jpe?g|webp)$/i.test(resolved), 'Use local PNG, JPEG, or WebP assets');
      const bytes = fs.readFileSync(resolved);
      const png = bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
      const jpeg = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
      const webp = bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP';
      assert(png || jpeg || webp, 'Invalid raster asset');
      const output = `assets/${assets.length + 1}${png ? '.png' : jpeg ? '.jpg' : '.webp'}`;
      assets.push({bytes, output});
      illustration = `<figure><img src="${output}" alt="${text(alt)}"><figcaption>${text(caption)}</figcaption></figure>`;
    }
    const bullets = section.bullets === undefined ? '' : (assert(Array.isArray(section.bullets)), `<ul>${section.bullets.map(item => `<li>${text(item)}</li>`).join('')}</ul>`);
    return `<section id="${section.id}"><h2>${text(section.heading)}</h2><p>${text(section.body)}</p>${bullets}${illustration}</section>`;
  }).join('\n');
  const html = `<!doctype html>
<html lang="${escape(page.language || 'en')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>${title}</title><meta name="description" content="${description}">
<style>*{box-sizing:border-box}body{margin:0;background:#f6f4ed;color:#192c31;font:1.15rem/1.6 system-ui,sans-serif;overflow-wrap:anywhere}main,footer{width:min(100% - 2.5rem,68rem);margin:auto}header{padding:5rem 0 3rem;border-bottom:2px solid #192c31}h1{font-size:clamp(2.4rem,6vw,4.8rem);line-height:1.08;max-width:18ch;letter-spacing:-.035em}h2{font-size:clamp(1.6rem,3vw,2.3rem);line-height:1.2}p,li{max-width:68ch;white-space:pre-line}.eyebrow{font-size:1rem;font-weight:650}.cta,button{display:inline-block;padding:.8rem 1.3rem;background:#174f45;color:white;border:2px solid #174f45;border-radius:.3rem;font:inherit;font-weight:650;text-decoration:none;max-width:100%}button:disabled{background:#dde4e0;color:#334c43;border-color:#334c43}a:focus-visible,button:focus-visible{outline:3px solid #9b3d0b;outline-offset:5px}section{padding:2.5rem 0;border-bottom:1px solid #abb8b1}figure{margin:2rem 0}img{display:block;max-width:100%;height:auto}figcaption{font-size:1rem;margin-top:.7rem}footer{padding:3rem 0}@media(max-width:480px){header{padding-top:2rem}.cta,button{width:100%;text-align:center}}
</style></head><body><main><header><p class="eyebrow">${title} · ${audience}</p><h1>${heading}</h1><p>${body}</p>${cta}</header>${sections}</main><footer>${cta}</footer></body></html>\n`;
  const parent = fs.realpathSync(path.dirname(path.resolve(destination)));
  const out = path.join(parent, path.basename(destination));
  const authorized = fs.realpathSync(workspace);
  assert(parent === authorized || parent.startsWith(authorized + path.sep), 'Output must be inside the authorized working directory');
  const plugin = fs.realpathSync(path.join(__dirname, '..'));
  assert(out !== plugin && !out.startsWith(plugin + path.sep), 'Output must be outside installed plugin');
  fs.mkdirSync(out);
  fs.mkdirSync(path.join(out, 'preview'));
  if (assets.length) fs.mkdirSync(path.join(out, 'preview/assets'));
  for (const asset of assets) fs.writeFileSync(path.join(out, 'preview', asset.output), asset.bytes, {flag:'wx'});
  fs.writeFileSync(path.join(out, 'preview/index.html'), html, {flag:'wx'});
  const copy = `# ${page.hero.heading}\n\n${page.hero.body}\n\n${page.sections.map(s => `## ${s.heading}\n\n${s.body}${s.bullets ? '\n\n' + s.bullets.map(b => '- ' + b).join('\n') : ''}`).join('\n\n')}\n\n${page.cta.text}${page.cta.url ? ': ' + page.cta.url : ''}\n`;
  fs.writeFileSync(path.join(out, 'landing-page.md'), copy, {flag:'wx'});
  fs.copyFileSync(source, path.join(out, 'page.json'), fs.constants.COPYFILE_EXCL);
  fs.writeFileSync(path.join(out, 'page-review.json'), JSON.stringify({stage:'page-generation',status:'partial',artifacts:['landing-page.md','preview/index.html'],checks:{html:'escaped text; no scripts or forms',visual:'not checked',cta:page.cta.url ? 'destination supplied; verification required' : 'missing destination; disabled preview button'},next_action:'Inspect desktop and narrow viewport; verify claims and CTA destination.'}, null, 2)+'\n', {flag:'wx'});
  return out;
}
if (require.main === module) {
  try { assert.equal(process.argv.length, 4, 'Usage: node render-page.js PAGE.json NEW_OUTPUT_DIR'); console.log(renderPage(process.argv[2], process.argv[3])); }
  catch (error) { console.error(`page-generation failed: ${error.message}`); process.exitCode = 1; }
}
module.exports = {renderPage};
