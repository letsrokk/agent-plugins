import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';

const root = fileURLToPath(new URL('../',import.meta.url));
const result = await build({absWorkingDir:root,entryPoints:['src/mcp_server.js'],outfile:'dist/mcp_server.js',bundle:true,platform:'node',target:'node24',format:'esm',write:false,metafile:true,legalComments:'inline',banner:{js:"import { createRequire as __createRequire } from 'node:module'; const require = __createRequire(import.meta.url);"}});
const packages = new Map();
for (const input of Object.keys(result.metafile.inputs)) {
  if (!input.startsWith('node_modules/')) continue;
  const parts = input.split('/');
  const directory = path.join(root,...parts.slice(0,parts[1].startsWith('@') ? 3 : 2));
  if (packages.has(directory)) continue;
  const manifest = JSON.parse(fs.readFileSync(path.join(directory,'package.json'),'utf8'));
  const licenseFile = fs.readdirSync(directory).find(name => /^(license|licence)(\.|$)/i.test(name));
  if (!licenseFile) throw new Error(`Missing license for bundled package ${manifest.name}`);
  packages.set(directory,`${manifest.name}@${manifest.version} (${manifest.license})\n\n${fs.readFileSync(path.join(directory,licenseFile),'utf8').trim()}\n`);
}
const notices = '# Bundled dependency licenses\n\n' + [...packages.entries()].sort(([a],[b]) => a < b ? -1 : a > b ? 1 : 0).map(([,notice]) => notice).join('\n---\n\n');
const artifacts = [[path.join(root,'dist/mcp_server.js'),result.outputFiles[0].contents],[path.join(root,'dist/THIRD_PARTY_NOTICES.txt'),Buffer.from(notices)]];
if (process.argv.includes('--check')) {
  for (const [file,content] of artifacts) if (!fs.existsSync(file) || !fs.readFileSync(file).equals(Buffer.from(content))) throw new Error(`Stale build artifact: ${path.relative(root,file)}; run npm run build`);
} else {
  fs.mkdirSync(path.join(root,'dist'),{recursive:true});
  for (const [file,content] of artifacts) fs.writeFileSync(file,content);
}
