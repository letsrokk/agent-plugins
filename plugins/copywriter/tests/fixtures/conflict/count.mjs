import { readFileSync } from 'node:fs';
const input = readFileSync(0, 'utf8');
console.log(input === '' ? 0 : input.split('\n').length - (input.endsWith('\n') ? 1 : 0));
