'use strict';

const fs = require('node:fs');
const { acquire, configuration, trustedContext } = require('./access.cjs');

(async () => {
  trustedContext(process.env);
  const config = configuration(process.env);
  const cidr = await acquire(config, {
    saveState: (key, value) => fs.appendFileSync(process.env.GITHUB_STATE, `${key}=${value}\n`),
    output: (key, value) => fs.appendFileSync(process.env.GITHUB_OUTPUT, `${key}=${value}\n`),
  });
  console.log(`Temporary SSH access verified for runner ${cidr}.`);
})().catch((error) => {
  console.error(`Firewall authorization failed: ${error.message}`);
  process.exitCode = 1;
});
