'use strict';

const net = require('node:net');

const API = 'https://api.digitalocean.com/v2/firewalls/';
const REPOSITORIES = new Set([
  'poliedrosoftware/odoo',
  'poliedrosoftware/odoo-holdinglalabranza',
]);
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function addressNumber(address) {
  if (!net.isIPv4(address)) throw new Error('Expected a single IPv4 address');
  return address.split('.').reduce((value, octet) => value * 256 + Number(octet), 0);
}

function inRange(address, range) {
  const [network, bitsText] = range.split('/');
  const bits = Number(bitsText);
  if (!net.isIPv4(network) || !/^\d+$/.test(bitsText || '') || bits < 0 || bits > 32) {
    throw new Error('Invalid IPv4 CIDR');
  }
  const size = 2 ** (32 - bits);
  return Math.floor(addressNumber(address) / size) === Math.floor(addressNumber(network) / size);
}

function publicAddress(address) {
  addressNumber(address);
  const excluded = [
    '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
    '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.0.2.0/24',
    '192.168.0.0/16', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24',
    '224.0.0.0/3',
  ];
  if (excluded.some((range) => inRange(address, range))) throw new Error('Expected a public IPv4 address');
  return address;
}

function configuration(env) {
  const firewallId = env['INPUT_FIREWALL-ID'] || '';
  const dropletId = env['INPUT_DROPLET-ID'] || '';
  const token = env.INPUT_TOKEN || '';
  const host = publicAddress(env.INPUT_HOST || '');
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(firewallId)) {
    throw new Error('Invalid firewall ID');
  }
  if (!/^[1-9]\d*$/.test(dropletId)) throw new Error('Invalid droplet ID');
  if (!token || /[\r\n]/.test(token)) throw new Error('Missing or invalid DO_FIREWALL_TOKEN');
  return { firewallId, dropletId: Number(dropletId), token, host };
}

function trustedContext(env) {
  if (env.GITHUB_ACTIONS !== 'true' || env.RUNNER_ENVIRONMENT !== 'github-hosted' ||
      env.GITHUB_REF !== 'refs/heads/main' ||
      !['push', 'workflow_dispatch'].includes(env.GITHUB_EVENT_NAME) ||
      !REPOSITORIES.has((env.GITHUB_REPOSITORY || '').toLowerCase())) {
    throw new Error('Firewall access is restricted to approved main-branch deployment jobs');
  }
}

async function jsonRequest(url, options, fetcher) {
  const response = await fetcher(url, { ...options, redirect: 'error', signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Remote API returned HTTP ${response.status}`);
  return response.status === 204 ? null : response.json();
}

function api(config, method, suffix, body, fetcher = fetch) {
  return jsonRequest(API + config.firewallId + suffix, {
    method,
    headers: { Authorization: `Bearer ${config.token}`, 'Content-Type': 'application/json' },
    ...(body ? { body: JSON.stringify(body) } : {}),
  }, fetcher);
}

function isolatedFirewall(firewall, dropletId) {
  if (!firewall || firewall.droplet_ids?.length !== 1 ||
      firewall.droplet_ids[0] !== dropletId || firewall.tags?.length) {
    throw new Error('The firewall must apply exclusively to the expected droplet');
  }
}

function hasRule(firewall, cidr) {
  return (firewall.inbound_rules || []).some((rule) =>
    rule.protocol === 'tcp' && rule.ports === '22' &&
    (!rule.action || rule.action === 'allow') && rule.sources?.addresses?.includes(cidr));
}

function ruleBody(cidr) {
  const address = cidr.replace(/\/32$/, '');
  if (cidr !== `${publicAddress(address)}/32`) throw new Error('Only a single IPv4 /32 may be authorized');
  return { inbound_rules: [{ protocol: 'tcp', ports: '22', action: 'allow', sources: { addresses: [cidr] } }] };
}

async function acquire(config, { saveState, output, fetcher = fetch, waitForSsh = waitForPort }) {
  const ipInfo = await jsonRequest('https://api.ipify.org?format=json', {}, fetcher);
  const address = publicAddress(ipInfo.ip);
  const meta = await jsonRequest('https://api.github.com/meta', {
    headers: { 'User-Agent': 'poliedro-deployment-firewall' },
  }, fetcher);
  if (!Array.isArray(meta.actions) || !meta.actions.some((range) =>
    range.includes('.') && inRange(address, range))) {
    throw new Error('Runner IP is not in the current GitHub Actions IPv4 ranges');
  }
  const { firewall } = await api(config, 'GET', '', null, fetcher);
  isolatedFirewall(firewall, config.dropletId);
  const cidr = `${address}/32`;
  // Existing permissions are not owned by this action and must never be removed.
  if (!hasRule(firewall, cidr)) {
    // Save ownership BEFORE the POST, including ambiguous timeout/failure cases.
    saveState('firewall_id', config.firewallId);
    saveState('droplet_id', String(config.dropletId));
    saveState('cidr', cidr);
    saveState('remove_rule', 'true');
    await api(config, 'POST', '/rules', ruleBody(cidr), fetcher);
  }
  output('runner-ip', address);
  await waitForSsh(config.host);
  return cidr;
}

async function release(config, state, { fetcher = fetch, sleep = delay } = {}) {
  if (state.remove_rule !== 'true') return false;
  if (state.firewall_id !== config.firewallId || Number(state.droplet_id) !== config.dropletId) {
    throw new Error('Saved firewall ownership does not match the action inputs');
  }
  const body = ruleBody(state.cidr);
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      const { firewall } = await api(config, 'GET', '', null, fetcher);
      isolatedFirewall(firewall, config.dropletId);
      if (!hasRule(firewall, state.cidr)) return true;
      await api(config, 'DELETE', '/rules', body, fetcher);
      const current = await api(config, 'GET', '', null, fetcher);
      if (!hasRule(current.firewall, state.cidr)) return true;
    } catch (error) {
      if (attempt === 3) throw error;
    }
    await sleep(2000 * (attempt + 1));
  }
  throw new Error('Temporary rule is still present; remove the reported /32 manually');
}

async function waitForPort(host) {
  for (let attempt = 0; attempt < 18; attempt++) {
    const connected = await new Promise((resolve) => {
      const socket = net.createConnection({ host, port: 22 });
      const finish = (ok) => { socket.destroy(); resolve(ok); };
      socket.setTimeout(3000, () => finish(false));
      socket.once('error', () => finish(false));
      socket.once('connect', () => finish(true));
    });
    if (connected) return;
    await delay(2000);
  }
  throw new Error('SSH did not become reachable after applying the temporary rule');
}

module.exports = {
  acquire, api, configuration, hasRule, inRange, isolatedFirewall,
  publicAddress, release, ruleBody, trustedContext,
};
