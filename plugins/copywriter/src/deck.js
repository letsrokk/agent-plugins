const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const PptxGenJS = require('pptxgenjs');
const imageSize = require('image-size');

function inside(root, target) {
  const relative = path.relative(root, target);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}
function localFile(root, name) {
  if (typeof name !== 'string' || !name || path.isAbsolute(name) || name.includes('\\') || name.split('/').includes('..') || /^[a-z]+:/i.test(name)) throw new Error('Expected a contained relative file path');
  const resolved = fs.realpathSync(path.resolve(root, name));
  if (!inside(root, resolved) || !fs.statSync(resolved).isFile()) throw new Error('Referenced file escapes input directory');
  return resolved;
}
function text(value, name, maximum = 10000) {
  if (typeof value !== 'string' || value.length > maximum || /[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(value)) throw new Error(`Invalid ${name}`);
  return value;
}
function index(items, label) {
  if (!Array.isArray(items)) throw new Error(`Expected ${label} array`);
  const result = new Map();
  for (const item of items) {
    if (!item || typeof item.id !== 'string' || !/^[A-Za-z0-9_-]+$/.test(item.id) || result.has(item.id)) throw new Error(`Invalid or duplicate ${label} ID`);
    result.set(item.id, item);
  }
  return result;
}
function validateSvg(source) {
  const tags = new Set('svg g title desc rect circle ellipse line polyline polygon path text tspan defs marker'.split(' '));
  const attributes = new Set('xmlns viewBox width height x y x1 y1 x2 y2 cx cy r rx ry d points fill stroke stroke-width stroke-linecap stroke-linejoin opacity fill-opacity stroke-opacity transform font-family font-size font-weight text-anchor dominant-baseline id role aria-labelledby aria-describedby markerWidth markerHeight refX refY orient markerUnits marker-end'.split(' '));
  const stack = [];
  let rootSeen = false;
  const tokens = source.match(/<[^>]*>|[^<]+/g) || [];
  if (tokens.join('') !== source || source.length > 1000000) throw new Error('Invalid safe SVG source');
  for (const token of tokens) {
    if (!token.startsWith('<')) {
      if ((!stack.length && token.trim()) || /&(?!(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);)/.test(token)) throw new Error('Invalid safe SVG text');
      continue;
    }
    const tag = token.match(/^<(\/?)([A-Za-z][A-Za-z0-9-]*)([\s\S]*?)(\/?)>$/);
    if (!tag || !tags.has(tag[2])) throw new Error('Unsupported or unsafe SVG element');
    const [, closing, name, raw, selfClosing] = tag;
    if (closing) {
      if (raw.trim() || selfClosing || stack.pop() !== name) throw new Error('Invalid SVG nesting');
      continue;
    }
    if (!stack.length) {
      if (rootSeen || name !== 'svg') throw new Error('Expected a single SVG root');
      rootSeen = true;
    }
    const seen = new Set();
    let rest = raw;
    while (rest.trim()) {
      const attribute = rest.match(/^\s+([A-Za-z][A-Za-z0-9-]*)\s*=\s*(["'])([^<>]*?)\2/);
      if (!attribute) throw new Error('Invalid SVG attribute');
      const [, key, , value] = attribute;
      if (!attributes.has(key) || seen.has(key) || /[&\x00-\x1F]/.test(value)) throw new Error('Unsupported or unsafe SVG attribute');
      if (key === 'xmlns' ? value !== 'http://www.w3.org/2000/svg' : /(?:url\s*\(|:|\\)/i.test(value) && !(key === 'marker-end' && /^url\(#[A-Za-z][A-Za-z0-9_-]*\)$/.test(value))) throw new Error('External SVG references are forbidden');
      seen.add(key);
      rest = rest.slice(attribute[0].length);
    }
    if (!selfClosing) stack.push(name);
  }
  if (!rootSeen || stack.length) throw new Error('Invalid SVG document');
}
function validate(model, base) {
  text(model.title, 'deck title', 200);
  if (model.language !== undefined && (typeof model.language !== 'string' || !/^[a-z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(model.language))) throw new Error('Invalid language tag');
  if (model.fontFace !== undefined) text(model.fontFace, 'font', 100);
  const claims = index(model.claims, 'claims');
  const assets = index(model.assets, 'assets');
  const slides = index(model.slides, 'slides');
  if (!slides.size || slides.size > 100) throw new Error('Expected 1–100 supported slides');
  const titles = new Set();
  const files = new Set();
  for (const asset of assets.values()) {
    const file = localFile(base, asset.file);
    if (!/\.(png|jpe?g)$/i.test(file)) throw new Error('Deck images must be PNG or JPEG; render diagrams to PNG and retain source separately');
    const signature = fs.readFileSync(file).subarray(0, 8);
    if (!(signature.equals(Buffer.from([137,80,78,71,13,10,26,10])) || (signature[0] === 255 && signature[1] === 216 && signature[2] === 255))) throw new Error('Invalid raster image signature');
    text(asset.alt, 'image alternative');
    if (!asset.alt.trim()) throw new Error('Informative images require alt text');
    files.add(asset.file);
    if (asset.source_file) {
      if (!/\.(mmd|svg|json|csv)$/i.test(asset.source_file)) throw new Error('Retained sources must be Mermaid, safe SVG, JSON, or CSV');
      const source = localFile(base, asset.source_file);
      if (/\.svg$/i.test(source)) validateSvg(fs.readFileSync(source, 'utf8'));
      files.add(asset.source_file);
    }
  }
  for (const slide of slides.values()) {
    text(slide.title, 'slide title', 160);
    if (!slide.title.trim() || titles.has(slide.title)) throw new Error('Slide titles must be unique and non-empty');
    titles.add(slide.title);
    text(slide.body, 'slide body', 1400);
    text(slide.notes, 'speaker notes');
    if (!['title', 'statement', 'two-column', 'image', 'diagram', 'chart', 'closing', 'sources', 'appendix'].includes(slide.layout)) throw new Error('Unknown slide layout');
    for (const [refs, known] of [[slide.claim_ids, claims], [slide.asset_ids, assets]]) {
      if (!Array.isArray(refs) || refs.some(id => !known.has(id))) throw new Error('Missing claim or asset reference');
    }
    if (slide.layout === 'two-column') {
      if (!Array.isArray(slide.columns) || slide.columns.length !== 2) throw new Error('Two-column slide requires two columns');
      for (const column of slide.columns) { text(column.title, 'column title', 100); text(column.body, 'column body', 650); }
    }
    if (['image', 'diagram'].includes(slide.layout) && slide.asset_ids.length !== 1) throw new Error('Image slide requires exactly one asset');
    if (slide.layout === 'chart') {
      const chart = slide.chart;
      if (!chart || !['bar', 'line'].includes(chart.type)) throw new Error('Chart type must be bar or line');
      text(chart.alt, 'chart alternative');
      if (!chart.alt.trim()) throw new Error('Chart alternative is required');
      if (typeof chart.file !== 'string' || !chart.file.endsWith('.json')) throw new Error('Chart data must be local JSON');
      const data = JSON.parse(fs.readFileSync(localFile(base, chart.file), 'utf8'));
      for (const field of ['units', 'source', 'method']) if (!text(data[field], `chart ${field}`).trim()) throw new Error(`Chart ${field} is required`);
      if (!Array.isArray(data.labels) || !data.labels.length || data.labels.length > 20 || data.labels.some(label => typeof label !== 'string' || !label)) throw new Error('Chart labels are required (maximum 20)');
      if (!Array.isArray(data.series) || !data.series.length || data.series.length > 4 || data.series.some(series => typeof series.name !== 'string' || !series.name || !Array.isArray(series.values) || series.values.length !== data.labels.length || series.values.some(value => typeof value !== 'number' || !Number.isFinite(value)))) throw new Error('Invalid chart series or values');
      files.add(chart.file);
    }
  }
  for (const name of files) {
    if (['pitch-deck.pptx', 'slides.json', 'speaker-notes.md', 'render-status.json', 'pitch-deck.pdf', 'previews'].includes(path.normalize(name).split(path.sep)[0])) throw new Error('Asset conflicts with generated output');
  }
  return { assets, files };
}
function processOutcome(result, produced, tool) {
  const error = result.error?.code;
  const state = error === 'ENOENT' ? 'unavailable' : error === 'ETIMEDOUT' ? 'timed out' : result.status !== 0 || error ? 'check failed' : !produced ? 'missing output' : 'generated';
  return {
    status: state,
    exit_status: Number.isInteger(result.status) ? result.status : null,
    error_code: error || null,
    signal: result.signal || null,
    stderr: (result.stderr || '').trim().slice(0, 1024),
    cause: state === 'generated' ? null : state === 'unavailable' ? `${tool} was not found` : state === 'timed out' ? `${tool} exceeded its time limit` : state === 'missing output' ? `${tool} exited successfully without all expected files` : `${tool} failed; inspect exit status and stderr`,
    next_action: state === 'generated' ? 'Inspect every rendered slide.' : state === 'unavailable' ? `Select an authorized setup path for ${tool}, then rerun the preserved deck.` : `Resolve the reported ${tool} failure and retry rendering the preserved deck.`
  };
}
async function renderDeck(input, output, workspace = process.cwd()) {
  const base = fs.realpathSync(path.dirname(path.resolve(input)));
  const model = JSON.parse(fs.readFileSync(input, 'utf8'));
  const { assets, files } = validate(model, base);
  const root = fs.realpathSync(workspace);
  const out = path.resolve(output);
  const parent = fs.realpathSync(path.dirname(out));
  if (inside(path.resolve(__dirname, '..'), parent)) throw new Error('Output cannot be inside the installed plugin');
  if (!inside(root, parent) || out === root || fs.existsSync(out)) throw new Error('Output must be a new directory inside the authorized working directory, with an existing parent');
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.author = '';
  pptx.subject = '';
  pptx.title = model.title;
  pptx.company = '';
  pptx.lang = model.language || 'en-US';
  pptx.theme = { headFontFace: model.fontFace || 'Arial', bodyFontFace: model.fontFace || 'Arial', lang: model.language || 'en-US' };
  const notes = [];
  for (const [i, item] of model.slides.entries()) {
    const slide = pptx.addSlide();
    slide.background = { color: 'F7F8FA' };
    const addText = (value, x, y, w, h, size = 24, extra = {}) => slide.addText(value, { x, y, w, h, lang: model.language || 'en-US', fontSize: size, color: '152336', margin: 0, breakLine: false, valign: 'top', ...extra });
    addText(item.title, 0.65, 0.45, 12, 1.1, 32, { bold: true, objectName: 'Slide title' });
    if (item.layout === 'two-column') {
      addText(item.body, 0.65, 1.65, 12, 0.75, 22);
      item.columns.forEach((column, n) => { addText(column.title, 0.65 + n * 6.2, 2.6, 5.7, 0.7, 26, { bold: true }); addText(column.body, 0.65 + n * 6.2, 3.5, 5.7, 3); });
    } else if (['image', 'diagram'].includes(item.layout)) {
      const asset = assets.get(item.asset_ids[0]);
      const image = localFile(base, asset.file);
      const dimensions = imageSize(fs.readFileSync(image));
      const scale = Math.min(7.5 / dimensions.width, 4.7 / dimensions.height);
      const w = dimensions.width * scale, h = dimensions.height * scale;
      slide.addImage({ path: image, x: 0.65 + (7.5 - w) / 2, y: 1.8 + (4.7 - h) / 2, w, h, altText: asset.alt, objectName: asset.id });
      addText(item.body, 8.6, 1.85, 4, 4.7, 22);
    } else if (item.layout === 'chart') {
      const data = JSON.parse(fs.readFileSync(localFile(base, item.chart.file), 'utf8'));
      slide.addChart(pptx.ChartType[item.chart.type], data.series.map(series => ({ ...series, labels: data.labels })), { lang: model.language || 'en-US', x: 0.65, y: 1.8, w: 8.1, h: 4.6, altText: item.chart.alt, showLegend: true, legendPos: 'b', catAxisLabelFontSize: 16, valAxisLabelFontSize: 16, showValue: true, showCatName: false, showTitle: false, showDataTable: false, showValAxisTitle: true, valAxisTitle: data.units, chartColors: ['2463A5', '9F451F', '416C42', '6B4A91'] });
      addText(item.body, 9.05, 1.85, 3.6, 4.7, 22);
      addText(`Source: ${data.source}`, 0.65, 6.55, 11.8, 0.35, 12);
    } else addText(item.body, 0.65, 1.85, 12, 4.8, item.layout === 'title' ? 30 : 24);
    addText(String(i + 1), 12.2, 7, 0.45, 0.25, 11);
    slide.addNotes(item.notes);
    notes.push(`## ${i + 1}. ${item.title}\n\n${item.notes}\n`);
  }
  fs.mkdirSync(out);
  await pptx.writeFile({ fileName: path.join(out, 'pitch-deck.pptx'), compression: true });
  for (const name of files) {
    const destination = path.join(out, name);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(localFile(base, name), destination, fs.constants.COPYFILE_EXCL);
  }
  fs.writeFileSync(path.join(out, 'slides.json'), JSON.stringify(model, null, 2) + '\n');
  fs.writeFileSync(path.join(out, 'speaker-notes.md'), notes.join('\n'));
  const status = { stage: 'render', status: 'partial', pptx: 'generated', office: null, pdf: 'not checked', previews: 'not checked', visual_review: 'not checked', accessibility_checker: 'not checked' };
  const probes = ['soffice', '/Applications/LibreOffice.app/Contents/MacOS/soffice'].map(name => ({ name, result: spawnSync(name, ['--version'], { encoding: 'utf8', timeout: 10000 }) }));
  const office = probes.find(probe => probe.result.status === 0);
  status.office_detection = probes.map(probe => ({ tool: path.basename(probe.name), ...processOutcome(probe.result, probe.result.status === 0, 'LibreOffice') }));
  if (office) {
    status.office = office.result.stdout.trim().slice(0, 300);
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'copywriter-office-'));
    try {
      const result = spawnSync(office.name, [`-env:UserInstallation=${require('node:url').pathToFileURL(profile).href}`, '--headless', '--convert-to', 'pdf', '--outdir', out, path.join(out, 'pitch-deck.pptx')], { encoding: 'utf8', timeout: 120000 });
      status.pdf_result = processOutcome(result, fs.existsSync(path.join(out, 'pitch-deck.pdf')), 'LibreOffice');
      status.pdf = status.pdf_result.status;
      if (status.pdf === 'generated') {
        const previews = path.join(out, 'previews');
        fs.mkdirSync(previews);
        const preview = spawnSync('pdftoppm', ['-scale-to', '1600', '-png', path.join(out, 'pitch-deck.pdf'), path.join(previews, 'slide')], { encoding: 'utf8', timeout: 120000 });
        const count = fs.readdirSync(previews).filter(name => /^slide-\d+\.png$/.test(name)).length;
        status.preview_result = processOutcome(preview, count === model.slides.length, 'pdftoppm');
        status.previews = status.preview_result.status;
      }
    } finally { fs.rmSync(profile, { recursive: true, force: true }); }
  } else {
    status.pdf = 'unavailable';
    status.next_action = 'Select an authorized LibreOffice setup path, then render and visually inspect the preserved PPTX.';
  }
  fs.writeFileSync(path.join(out, 'render-status.json'), JSON.stringify(status, null, 2) + '\n');
  return status;
}
module.exports = { renderDeck, validate, processOutcome };
