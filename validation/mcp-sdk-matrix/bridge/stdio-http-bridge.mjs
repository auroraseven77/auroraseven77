import http from 'node:http';
import crypto from 'node:crypto';
import path from 'node:path';
import fs from 'node:fs';
import { bearerMatches, isLoopbackRequest, validateBridgeConfig } from './bridge-security.mjs';
import { filterAllowedTools, isToolAllowed } from './tool-policy.mjs';

const ALLOWED_METHODS = new Set(['POST', 'GET', 'DELETE']);
const MAX_CONTENT_LENGTH = 1024 * 1024;
const SESSION_TTL_MS = 10 * 60 * 1000;

function childEnvironment(sdkNodeModules) {
  const allowed = ['HOME', 'PATH', 'TMPDIR', 'PREFIX', 'ANDROID_DATA', 'ANDROID_ROOT', 'LANG', 'LC_ALL'];
  const env = {};
  for (const key of allowed) if (typeof process.env[key] === 'string') env[key] = process.env[key];
  env.NODE_PATH = sdkNodeModules;
  return env;
}

function readBearerToken(tokenFile) {
  const flags = fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0);
  const fd = fs.openSync(tokenFile, flags);
  try {
    const st = fs.fstatSync(fd);
    if (!st.isFile() || (st.mode & 0o077) !== 0 || (typeof process.getuid === 'function' && st.uid !== process.getuid())) {
      throw Object.assign(new Error('BRIDGE_TOKEN_FILE_PERMISSIONS'), { code: 'BRIDGE_TOKEN_FILE_PERMISSIONS' });
    }
    const token = fs.readFileSync(fd, 'utf8').trim();
    if (Buffer.byteLength(token) < 32) throw Object.assign(new Error('BRIDGE_TOKEN_TOO_SHORT'), { code: 'BRIDGE_TOKEN_TOO_SHORT' });
    return token;
  } finally { fs.closeSync(fd); }
}

export async function startAuroraBridge({
  sdk,
  upstreamServer,
  sdkNodeModules,
  token,
  host = '127.0.0.1',
  port = 0,
  maxSessions = 8,
  logger = () => {}
}) {
  const config = validateBridgeConfig({ token, bindHost: host, maxSessions });
  if (!sdk || !sdk.Client || !sdk.StdioClientTransport || !sdk.Server || !sdk.StreamableHTTPServerTransport || !sdk.ListToolsRequestSchema || !sdk.CallToolRequestSchema) {
    throw new Error('MCP_SDK_API_INCOMPLETE');
  }
  if (typeof upstreamServer !== 'string' || !path.isAbsolute(upstreamServer)) throw new Error('UPSTREAM_SERVER_PATH_REQUIRED');
  if (typeof sdkNodeModules !== 'string' || !path.isAbsolute(sdkNodeModules)) throw new Error('SDK_NODE_MODULES_PATH_REQUIRED');

  const upstreamTransport = new sdk.StdioClientTransport({
    command: process.execPath,
    args: [upstreamServer],
    env: childEnvironment(sdkNodeModules),
    stderr: 'inherit'
  });
  const upstream = new sdk.Client({ name: 'aurora-stdio-http-bridge', version: '1.0.0' }, { capabilities: {} });
  let initial;
  try {
    await upstream.connect(upstreamTransport);
    initial = await upstream.listTools();
  } catch {
    await upstream.close().catch(() => {});
    throw Object.assign(new Error('UPSTREAM_START_FAILED'), { code: 'UPSTREAM_START_FAILED' });
  }
  const advertised = new Set((initial.tools || []).map(t => t?.name).filter(n => typeof n === 'string'));
  const initialAllowed = filterAllowedTools(initial.tools || []);
  if (initialAllowed.length === 0) {
    await upstream.close().catch(() => {});
    throw new Error('UPSTREAM_HAS_NO_ALLOWED_TOOLS');
  }

  const sessions = new Map();
  let server;
  let closing = false;

  async function getAllowedTools() {
    let current;
    try { current = await upstream.listTools(); }
    catch { throw Object.assign(new Error('UPSTREAM_UNAVAILABLE'), { code: 'UPSTREAM_UNAVAILABLE' }); }
    const names = new Set((current.tools || []).map(t => t?.name).filter(n => typeof n === 'string'));
    advertised.clear();
    for (const name of names) advertised.add(name);
    return filterAllowedTools(current.tools || []);
  }

  function closeSession(session) {
    if (session.closePromise) return session.closePromise;
    session.closePromise = Promise.resolve().then(async () => {
      sessions.delete(session.id);
      await session.server.close().catch(() => {});
    });
    return session.closePromise;
  }

  async function pruneExpiredSessions() {
    const now = Date.now();
    for (const session of [...sessions.values()]) {
      if (now - session.lastSeen > SESSION_TTL_MS) await closeSession(session);
    }
  }

  async function createSession() {
    await pruneExpiredSessions();
    if (sessions.size >= config.maxSessions) throw Object.assign(new Error('BRIDGE_SESSION_LIMIT'), { code: 'BRIDGE_SESSION_LIMIT' });
    const id = crypto.randomUUID();
    const transport = new sdk.StreamableHTTPServerTransport({ sessionIdGenerator: () => id });
    const mcpServer = new sdk.Server(
      { name: 'aurora-stdio-http-bridge', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );

    mcpServer.setRequestHandler(sdk.ListToolsRequestSchema, async () => ({ tools: await getAllowedTools() }));
    mcpServer.setRequestHandler(sdk.CallToolRequestSchema, async request => {
      const name = request.params?.name;
      const args = request.params?.arguments ?? {};
      if (typeof name !== 'string' || !advertised.has(name) || !isToolAllowed(name, args)) {
        return { isError: true, content: [{ type: 'text', text: JSON.stringify({ error: 'TOOL_POLICY_DENIED' }) }] };
      }
      let live;
      try { live = await upstream.listTools(); }
      catch { return { isError: true, content: [{ type: 'text', text: JSON.stringify({ error: 'UPSTREAM_UNAVAILABLE' }) }] }; }
      const liveNames = new Set((live.tools || []).map(t => t?.name));
      if (!liveNames.has(name)) return { isError: true, content: [{ type: 'text', text: JSON.stringify({ error: 'TOOL_NOT_ADVERTISED' }) }] };
      try { return await upstream.callTool({ name, arguments: args }); }
      catch { return { isError: true, content: [{ type: 'text', text: JSON.stringify({ error: 'UPSTREAM_UNAVAILABLE' }) }] }; }
    });

    const session = { id, transport, server: mcpServer, lastSeen: Date.now(), closePromise: null };
    sessions.set(id, session);
    try { await mcpServer.connect(transport); }
    catch (error) {
      sessions.delete(id);
      await mcpServer.close().catch(() => {});
      throw error;
    }
    return session;
  }

  server = http.createServer(async (req, res) => {
    const reject = (status, code) => {
      if (!res.headersSent) {
        res.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store' });
        res.end(JSON.stringify({ error: code }));
      } else res.destroy();
    };
    if (req.url !== '/mcp') return reject(404, 'NOT_FOUND');
    if (!ALLOWED_METHODS.has(req.method)) return reject(405, 'METHOD_NOT_ALLOWED');
    if (!bearerMatches(req.headers.authorization, config.token)) return reject(401, 'UNAUTHORIZED');
    const address = server.address();
    const actualPort = typeof address === 'object' && address ? address.port : port;
    if (!isLoopbackRequest(req, actualPort)) return reject(403, 'LOOPBACK_ORIGIN_REQUIRED');
    const contentLengthHeader = req.headers['content-length'];
    if (contentLengthHeader !== undefined) {
      if (typeof contentLengthHeader !== 'string' || !/^[0-9]+$/.test(contentLengthHeader)) return reject(400, 'CONTENT_LENGTH_INVALID');
      if (Number(contentLengthHeader) > MAX_CONTENT_LENGTH) return reject(413, 'REQUEST_TOO_LARGE');
    }

    const sessionId = req.headers['mcp-session-id'];
    let session;
    if (typeof sessionId === 'string') {
      session = sessions.get(sessionId);
      if (!session) return reject(404, 'SESSION_NOT_FOUND');
      if (Date.now() - session.lastSeen > SESSION_TTL_MS) { await closeSession(session); return reject(404, 'SESSION_EXPIRED'); }
      session.lastSeen = Date.now();
    } else {
      if (req.method !== 'POST') return reject(400, 'SESSION_REQUIRED');
      try { session = await createSession(); }
      catch (error) {
        const code = error?.code === 'BRIDGE_SESSION_LIMIT' ? 'BRIDGE_SESSION_LIMIT' : 'SESSION_CREATE_FAILED';
        return reject(code === 'BRIDGE_SESSION_LIMIT' ? 503 : 502, code);
      }
    }

    if (req.method === 'DELETE') {
      await closeSession(session);
      res.writeHead(200, { 'cache-control': 'no-store' });
      res.end();
      return;
    }

    try {
      await session.transport.handleRequest(req, res);
    } catch {
      reject(502, 'MCP_UPSTREAM_FAILURE');
    }
  });

  server.requestTimeout = 30_000;
  server.headersTimeout = 10_000;
  server.keepAliveTimeout = 5_000;
  server.maxHeadersCount = 32;
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(port, host, () => {
        server.removeListener('error', reject);
        resolve();
      });
    });
  } catch {
    await upstream.close().catch(() => {});
    throw Object.assign(new Error('BRIDGE_LISTEN_FAILED'), { code: 'BRIDGE_LISTEN_FAILED' });
  }
  const actual = server.address();
  logger('BRIDGE_LISTENING host=' + host + ' port=' + actual.port + ' tools=' + initialAllowed.map(t => t.name).join(','));

  return {
    host,
    port: actual.port,
    tools: initialAllowed,
    sessionCount: () => sessions.size,
    sessionIds: () => [...sessions.keys()],
    async close() {
      if (closing) return;
      closing = true;
      for (const session of [...sessions.values()]) await closeSession(session);
      sessions.clear();
      await upstream.close().catch(() => {});
      await new Promise(resolve => server.close(() => resolve()));
    }
  };
}

export { readBearerToken };
