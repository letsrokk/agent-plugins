#!/usr/bin/env node
const { renderDeck } = require('../vendor/deck.cjs');
if (process.argv.length !== 4) {
  console.error('Usage: node render-deck.js slides.json NEW_OUTPUT_DIRECTORY');
  process.exitCode = 1;
} else renderDeck(process.argv[2], process.argv[3]).then(status => console.log(JSON.stringify(status, null, 2))).catch(error => {
  console.error(`Deck generation failed: ${error.message}`);
  process.exitCode = 1;
});
