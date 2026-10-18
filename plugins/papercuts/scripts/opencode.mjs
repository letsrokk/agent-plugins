import { sessionContext } from './session_context.js';

export default async function () {
  return {
    'experimental.chat.system.transform': async (_input, output) => {
      output.system.push(sessionContext());
    },
    'experimental.session.compacting': async (_input, output) => {
      output.context.push(sessionContext());
    },
  };
}
