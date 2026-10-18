#!/usr/bin/env node
'use strict';
const { sessionContext } = require('./session_context.js');

try {
  const additionalContext = sessionContext();
  const output = process.argv.includes('--copilot')
    ? { additionalContext }
    : { hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext } };
  console.log(JSON.stringify(output));
} catch (error) {
  console.error(`read-the-room could not load its writing policy: ${error.message}`);
  process.exitCode = 1;
}
