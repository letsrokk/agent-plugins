import { readFileSync } from 'node:fs';
const input = readFileSync(0, 'utf8');
const count = input === '' ? 0 : input.split('\n').length - (input.endsWith('\n') ? 1 : 0);
console.log(count);
