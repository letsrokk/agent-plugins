import { sessionContext } from './session_context.js';

export default function (pi) {
  pi.on('before_agent_start', event => {
    event.systemPromptOptions.sections['read-the-room'] = sessionContext();
  });
}
