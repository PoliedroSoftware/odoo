'use strict';

const { configuration, release } = require('./access.cjs');

(async () => {
  if (process.env.STATE_remove_rule !== 'true') return;
  const state = Object.fromEntries(['remove_rule', 'firewall_id', 'droplet_id', 'cidr']
    .map((key) => [key, process.env[`STATE_${key}`]]));
  await release(configuration(process.env), state);
  console.log(`Temporary SSH rule removed: ${state.cidr}.`);
})().catch((error) => {
  console.error(`FIREWALL CLEANUP FAILED: ${error.message}. Check the action's runner /32 immediately.`);
  process.exitCode = 1;
});
