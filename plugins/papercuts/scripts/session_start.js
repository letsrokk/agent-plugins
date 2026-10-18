#!/usr/bin/env node
import { sessionContext } from './session_context.js';

try {
  const additionalContext = sessionContext();
  const output = process.argv.includes('--copilot')
    ? { additionalContext }
    : { hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext } };
  console.log(JSON.stringify(output));
} catch (error) {
  console.error(`papercuts could not load its instructions: ${error.message}`);
  process.exitCode = 1;
}
