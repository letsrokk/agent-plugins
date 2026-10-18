import { fileURLToPath } from 'node:url';
import { sessionContext } from './session_context.js';

export default function (pi) {
  pi.registerMcpServer('papercuts', {
    command: 'node',
    args: [fileURLToPath(new URL('../dist/mcp_server.js', import.meta.url))],
    env: { PAPERCUTS_CLIENT: 'pi' },
    exposure: 'direct',
  });
  pi.on('before_agent_start', event => {
    event.systemPromptOptions.sections['papercuts'] = sessionContext();
  });
}
