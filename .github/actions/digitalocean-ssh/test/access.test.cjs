'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const { acquire, configuration, inRange, publicAddress, release, ruleBody, trustedContext } = require('../access.cjs');
const config = { token: 'fake-test-token', firewallId: 'cf8761d8-6808-4268-b4d3-a2886223406d', dropletId: 608212229, host: '138.197.65.167' };
const runner = '20.30.40.50';
const owner = '8.8.8.8/32'; // Fixture only; never the operator's real address.
const context = { GITHUB_ACTIONS: 'true', RUNNER_ENVIRONMENT: 'github-hosted', GITHUB_REF: 'refs/heads/main', GITHUB_EVENT_NAME: 'push', GITHUB_REPOSITORY: 'PoliedroSoftware/odoo' };

function fixture({ existing = false, outside = false, extraDroplet = false, postFails = false, waitFails = false } = {}) {
  const state = {};
  const calls = [];
  const rules = new Set([owner, ...(existing ? [`${runner}/32`] : [])]);
  const fetcher = async (url, options = {}) => {
    calls.push({ url, method: options.method || 'GET', body: options.body, headers: options.headers });
    let result;
    if (url.startsWith('https://api.ipify.org')) result = { ip: runner };
    else if (url === 'https://api.github.com/meta') result = { actions: [outside ? '30.0.0.0/8' : '20.0.0.0/8', '2603::/24'] };
    else if (!url.endsWith('/rules')) result = { firewall: {
      droplet_ids: extraDroplet ? [config.dropletId, 123] : [config.dropletId], tags: [],
      inbound_rules: [...rules].map((address) => ({ protocol: 'tcp', ports: '22', sources: { addresses: [address] } })),
    } };
    else {
      const cidr = JSON.parse(options.body).inbound_rules[0].sources.addresses[0];
      if (options.method === 'POST') { rules.add(cidr); if (postFails) throw new Error('ambiguous timeout'); }
      else if (options.method === 'DELETE') rules.delete(cidr);
      return { ok: true, status: 204 };
    }
    return { ok: true, status: 200, json: async () => structuredClone(result) };
  };
  return { state, calls, rules, fetcher, options: {
    fetcher, saveState: (key, value) => { state[key] = value; }, output: () => {},
    waitForSsh: async () => { if (waitFails) throw new Error('SSH blocked'); },
  } };
}

test('only exact /32 rules on TCP 22 are constructed', () => {
  assert.deepEqual(ruleBody(`${runner}/32`).inbound_rules[0], {
    protocol: 'tcp', ports: '22', action: 'allow', sources: { addresses: [`${runner}/32`] },
  });
  for (const cidr of ['0.0.0.0/0', `${runner}/24`, '10.0.0.1/32']) assert.throws(() => ruleBody(cidr));
});
test('private, reserved and IPv6 addresses are rejected', () => {
  for (const ip of ['127.0.0.1', '10.2.3.4', '192.168.1.1', '100.64.0.1', '198.51.100.8', '::1', '224.0.0.1', '1.2.3.999']) assert.throws(() => publicAddress(ip));
  assert.equal(publicAddress(runner), runner);
  assert.equal(inRange(runner, '20.0.0.0/8'), true);
  assert.equal(inRange(runner, '21.0.0.0/8'), false);
});
test('pull requests, branches and unrelated repositories cannot authorize SSH', () => {
  assert.doesNotThrow(() => trustedContext(context));
  for (const patch of [{ GITHUB_REF: 'refs/heads/test' }, { GITHUB_EVENT_NAME: 'pull_request' }, { GITHUB_REPOSITORY: 'other/repo' }, { RUNNER_ENVIRONMENT: 'self-hosted' }]) assert.throws(() => trustedContext({ ...context, ...patch }));
});
test('invalid input and a missing limited token fail closed', () => {
  const input = { INPUT_TOKEN: config.token, 'INPUT_FIREWALL-ID': config.firewallId, 'INPUT_DROPLET-ID': String(config.dropletId), INPUT_HOST: config.host };
  assert.deepEqual(configuration(input), config);
  assert.throws(() => configuration({ ...input, INPUT_TOKEN: '' }));
  assert.throws(() => configuration({ ...input, 'INPUT_FIREWALL-ID': '../other' }));
});
test('acquire and cleanup preserve the administrator rule', async () => {
  const f = fixture();
  await acquire(config, f.options);
  assert(f.rules.has(`${runner}/32`));
  assert.equal(await release(config, f.state, { fetcher: f.fetcher }), true);
  assert.deepEqual([...f.rules], [owner]);
  for (const call of f.calls.filter((c) => !c.url.startsWith('https://api.digitalocean.com'))) assert.equal(call.headers?.Authorization, undefined);
});
test('pre-existing authorization is never owned or removed', async () => {
  const f = fixture({ existing: true });
  await acquire(config, f.options);
  assert.equal(await release(config, f.state, { fetcher: f.fetcher }), false);
  assert(f.rules.has(`${runner}/32`));
  assert(!f.calls.some((c) => c.method === 'DELETE'));
});
test('an IP outside GitHub Actions fails before changing the firewall', async () => {
  const f = fixture({ outside: true });
  await assert.rejects(acquire(config, f.options), /not in the current GitHub/);
  assert(!f.calls.some((c) => c.method === 'POST'));
});
test('a shared firewall fails before any mutation', async () => {
  const f = fixture({ extraDroplet: true });
  await assert.rejects(acquire(config, f.options), /exclusively/);
  assert(!f.calls.some((c) => c.method === 'POST'));
});
test('an ambiguous POST failure still records and cleans the rule', async () => {
  const f = fixture({ postFails: true });
  await assert.rejects(acquire(config, f.options), /ambiguous/);
  assert.equal(f.state.remove_rule, 'true');
  await release(config, f.state, { fetcher: f.fetcher });
  assert.deepEqual([...f.rules], [owner]);
});
test('SSH propagation failure is followed by cleanup', async () => {
  const f = fixture({ waitFails: true });
  await assert.rejects(acquire(config, f.options), /SSH blocked/);
  await release(config, f.state, { fetcher: f.fetcher });
  assert.deepEqual([...f.rules], [owner]);
});
test('cleanup rejects ownership of another firewall', async () => {
  const f = fixture();
  await acquire(config, f.options);
  await assert.rejects(release(config, { ...f.state, droplet_id: '123' }, { fetcher: f.fetcher }), /does not match/);
});
test('cleanup is idempotent', async () => {
  const f = fixture();
  await acquire(config, f.options);
  await release(config, f.state, { fetcher: f.fetcher });
  await release(config, f.state, { fetcher: f.fetcher });
  assert.deepEqual([...f.rules], [owner]);
});
