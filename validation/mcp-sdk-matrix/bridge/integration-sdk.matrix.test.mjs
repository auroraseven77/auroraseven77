import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { startAuroraBridge } from './stdio-http-bridge.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const NODE_MODULES = path.join(HERE, 'node_modules');
const SDK = { Client, StdioClientTransport, Server, StreamableHTTPServerTransport, ListToolsRequestSchema, CallToolRequestSchema };
const TOKEN = crypto.randomBytes(32).toString('hex');
const UPSTREAM = process.env.AURORA_UPSTREAM_SERVER;
const sdkPackage = JSON.parse(fs.readFileSync(path.join(NODE_MODULES, '@modelcontextprotocol', 'sdk', 'package.json'), 'utf8'));
const EXPECTED_SDK_VERSION = process.env.AURORA_EXPECTED_SDK_VERSION || '1.30.1';
const EXPECTED_UPSTREAM_SHA256 = 'f2468deedd188b6040801993963a48cc47a4fbaec05b89f56ef9a05a6af403c9';

function parseToolText(result) {
  const value = result.content?.find(item => item.type === 'text')?.text;
  assert.equal(typeof value, 'string', 'MCP text content expected');
  return value;
}

function rawPost(url, headers = {}, body = '{}') {
  const target = new URL(url);
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '127.0.0.1',
      port: Number(target.port),
      path: target.pathname,
      method: 'POST',
      headers: { 'content-type': 'application/json', ...headers }
    }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('error', reject);
    req.end(body);
  });
}

function rawChunkedPost(url, headers, body) {
  const target = new URL(url);
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '127.0.0.1',
      port: Number(target.port),
      path: target.pathname,
      method: 'POST',
      headers: { 'content-type': 'application/json', 'transfer-encoding': 'chunked', ...headers }
    }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.setTimeout(15000, () => req.destroy(new Error('chunked request timeout')));
    req.on('error', reject);
    req.end(body);
  });
}

async function connectClient(url, token = TOKEN) {
  const transport = new StreamableHTTPClientTransport(new URL(url), {
    requestInit: { headers: { Authorization: 'Bearer ' + token } }
  });
  const client = new Client({ name: 'aurora-bridge-integration-test', version: '1.0.0' }, { capabilities: {} });
  await client.connect(transport);
  return { client, transport };
}

async function terminateSession(endpoint, sessionId) {
  return fetch(endpoint, {
    method: 'DELETE',
    headers: {
      authorization: 'Bearer ' + TOKEN,
      'mcp-session-id': sessionId
    }
  });
}

test('actual SDK: STDIO upstream and authenticated Streamable HTTP bridge', { timeout: 45000 }, async t => {
  assert.equal(sdkPackage.version, EXPECTED_SDK_VERSION, 'integration must use the selected exact SDK version');
  assert.ok(UPSTREAM && path.isAbsolute(UPSTREAM), 'AURORA_UPSTREAM_SERVER must point to the pinned v1.0.1 server');
  assert.equal(
    crypto.createHash('sha256').update(fs.readFileSync(UPSTREAM)).digest('hex'),
    EXPECTED_UPSTREAM_SHA256,
    'the recovered server baseline must match its pinned SHA-256'
  );

  const bridge = await startAuroraBridge({
    sdk: SDK, upstreamServer: UPSTREAM, sdkNodeModules: NODE_MODULES,
    token: TOKEN, host: '127.0.0.1', port: 0
  });
  let client;
  t.after(async () => {
    await client?.close().catch(() => {});
    await bridge.close();
  });
  const endpoint = 'http://127.0.0.1:' + bridge.port + '/mcp';

  const initBody = JSON.stringify({
    jsonrpc: '2.0', id: 1, method: 'initialize',
    params: { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'unauth-test', version: '1' } }
  });
  assert.equal((await rawPost(endpoint, {}, initBody)).status, 401, 'missing Bearer must be rejected');
  assert.equal((await rawPost(endpoint, { authorization: 'Bearer wrong-token' })).status, 401, 'wrong Bearer must be rejected');
  assert.equal((await rawPost(endpoint, { authorization: 'Bearer ' + TOKEN, origin: 'https://attacker.example' })).status, 403, 'hostile Origin must be rejected');
  assert.equal((await rawPost(endpoint, { authorization: 'Bearer ' + TOKEN, host: 'attacker.example' })).status, 403, 'hostile Host must be rejected');

  ({ client } = await connectClient(endpoint));
  const listed = await client.listTools();
  assert.deepEqual(
    listed.tools.map(tool => tool.name).sort(),
    ['aurora.list_projects', 'aurora.read_evidence']
  );

  const projects = await client.callTool({ name: 'aurora.list_projects', arguments: {} });
  assert.notEqual(projects.isError, true);
  const projectData = JSON.parse(parseToolText(projects));
  assert.equal(projectData.length, 6);
  assert.ok(projectData.every(project => project.exists === true));

  const evidence = await client.callTool({
    name: 'aurora.read_evidence',
    arguments: { project: 'auroraseven77-test', relative_path: 'CHANGELOG.md' }
  });
  assert.notEqual(evidence.isError, true);
  const evidenceData = JSON.parse(parseToolText(evidence));
  assert.equal(evidenceData.project, 'auroraseven77-test');
  assert.equal(evidenceData.bytes, Buffer.byteLength(evidenceData.content));
  assert.match(evidenceData.sha256, /^[a-f0-9]{64}$/);

  const denied = await client.callTool({
    name: 'aurora.read_evidence',
    arguments: { project: 'auroraseven77-test', relative_path: '.env' }
  });
  assert.equal(denied.isError, true, 'sensitive path must be denied by bridge policy');

  const shellDenied = await client.callTool({ name: 'exec_command', arguments: { command: 'id' } });
  assert.equal(shellDenied.isError, true, 'unlisted command tool must be denied');

  const missing = await client.callTool({
    name: 'aurora.read_evidence',
    arguments: { project: 'auroraseven77-test', relative_path: 'AURORA-NO-SUCH-FILE-20261030.txt' }
  });
  assert.equal(missing.isError, true, 'upstream filesystem failure must remain a tool error');

  const invalidSession = await fetch(endpoint, {
    method: 'POST',
    headers: {
      authorization: 'Bearer ' + TOKEN,
      'mcp-session-id': 'not-a-real-session',
      'content-type': 'application/json'
    },
    body: '{}'
  });
  assert.equal(invalidSession.status, 404, 'unknown MCP session must be rejected');

  const sessionId = bridge.sessionIds()[0];
  assert.equal(typeof sessionId, 'string', 'the test bridge must have one active session');
  const terminated = await terminateSession(endpoint, sessionId);
  assert.equal(terminated.status, 200, 'explicit MCP DELETE must terminate the session');
  assert.equal(bridge.sessionCount(), 0, 'explicit MCP DELETE must release server-side session resources');
  await client.close();
  client = undefined;
});

test('actual SDK: upstream discovery changes fail closed', { timeout: 30000 }, async t => {
  const fixture = path.join(HERE, 'fixtures', 'upstream-discovery-sequence.mjs');
  const bridge = await startAuroraBridge({
    sdk: SDK, upstreamServer: fixture, sdkNodeModules: NODE_MODULES,
    token: TOKEN, host: '127.0.0.1', port: 0
  });
  let client;
  t.after(async () => {
    await client?.close().catch(() => {});
    await bridge.close();
  });
  const endpoint = 'http://127.0.0.1:' + bridge.port + '/mcp';
  ({ client } = await connectClient(endpoint));
  const listed = await client.listTools();
  assert.deepEqual(listed.tools.map(tool => tool.name).sort(), ['aurora.list_projects', 'aurora.read_evidence']);
  const result = await client.callTool({
    name: 'aurora.read_evidence',
    arguments: { project: 'auroraseven77-test', relative_path: 'CHANGELOG.md' }
  });
  assert.equal(result.isError, true, 'a tool no longer advertised upstream must not be invoked');

  const sessionId = bridge.sessionIds()[0];
  assert.equal(typeof sessionId, 'string');
  const terminated = await terminateSession(endpoint, sessionId);
  assert.equal(terminated.status, 200);
  assert.equal(bridge.sessionCount(), 0);
  await client.close();
  client = undefined;
});

test('actual SDK: bridge rejects non-loopback bind addresses', async () => {
  await assert.rejects(
    () => startAuroraBridge({
      sdk: SDK,
      upstreamServer: UPSTREAM || '/tmp/no-server',
      sdkNodeModules: NODE_MODULES,
      token: TOKEN,
      host: '0.0.0.0',
      port: 0
    }),
    error => error.code === 'BRIDGE_BIND_HOST_DENIED'
  );
});

test('actual SDK: oversized chunked HTTP request body is rejected', { timeout: 45000 }, async t => {
  assert.equal(sdkPackage.version, EXPECTED_SDK_VERSION);
  assert.ok(UPSTREAM && path.isAbsolute(UPSTREAM));
  const bridge = await startAuroraBridge({
    sdk: SDK, upstreamServer: UPSTREAM, sdkNodeModules: NODE_MODULES,
    token: TOKEN, host: '127.0.0.1', port: 0
  });
  t.after(async () => { await bridge.close(); });
  const endpoint = 'http://127.0.0.1:' + bridge.port + '/mcp';
  const body = JSON.stringify({
    jsonrpc: '2.0',
    method: 'notifications/initialized',
    params: { padding: 'x'.repeat(5 * 1024 * 1024) }
  });
  const result = await rawChunkedPost(endpoint, { authorization: 'Bearer ' + TOKEN }, body)
    .catch(error => ({ status: 0, transportError: error.code || error.message }));
  assert.ok(
    result.status === 0 || result.status >= 400,
    'chunked body above 5 MiB must be rejected; HTTP status was ' + result.status
  );
});
