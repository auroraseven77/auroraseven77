import crypto from 'node:crypto';
import net from 'node:net';

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost']);

export function bearerMatches(header, expected) {
  if (typeof header !== 'string' || typeof expected !== 'string' || !expected) return false;
  const match = /^Bearer ([A-Za-z0-9._~+/-]+=*)$/.exec(header);
  if (!match) return false;
  const actual = Buffer.from(match[1]);
  const wanted = Buffer.from(expected);
  return actual.length === wanted.length && crypto.timingSafeEqual(actual, wanted);
}

function parseLoopbackAuthority(value) {
  if (typeof value !== 'string' || value.length > 255) return null;
  try {
    const url = new URL('http://' + value);
    if (url.username || url.password || url.pathname !== '/' || url.search || url.hash) return null;
    const hostname = url.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (!LOOPBACK_HOSTS.has(hostname) && !(net.isIP(hostname) === 6 && hostname === '::1')) return null;
    return { hostname, port: url.port || '80' };
  } catch { return null; }
}

export function isLoopbackRequest(req, expectedPort) {
  const host = parseLoopbackAuthority(req.headers.host);
  if (!host || host.port !== String(expectedPort)) return false;
  const origin = req.headers.origin;
  if (origin === undefined) return true;
  if (typeof origin !== 'string') return false;
  let parsed;
  try { parsed = new URL(origin); } catch { return false; }
  if (parsed.protocol !== 'http:' || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) return false;
  const originHost = parseLoopbackAuthority(parsed.host);
  return Boolean(originHost && originHost.port === String(expectedPort));
}

export function validateBridgeConfig({ token, bindHost = '127.0.0.1', maxSessions = 8 }) {
  if (typeof token !== 'string' || Buffer.byteLength(token) < 32) {
    throw Object.assign(new Error('BRIDGE_TOKEN_TOO_SHORT'), { code: 'BRIDGE_TOKEN_TOO_SHORT' });
  }
  if (bindHost !== '127.0.0.1') {
    throw Object.assign(new Error('BRIDGE_BIND_HOST_DENIED'), { code: 'BRIDGE_BIND_HOST_DENIED' });
  }
  if (!Number.isInteger(maxSessions) || maxSessions < 1 || maxSessions > 32) {
    throw Object.assign(new Error('BRIDGE_SESSION_LIMIT_INVALID'), { code: 'BRIDGE_SESSION_LIMIT_INVALID' });
  }
  return Object.freeze({ token, bindHost, maxSessions });
}
