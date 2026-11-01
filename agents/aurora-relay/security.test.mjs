import test from 'node:test';
import assert from 'node:assert/strict';
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  utimesSync,
  writeFileSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import {
  assertInboxLimit,
  parseApprovePublishArg,
  readRequest,
  safeWriteAtomic,
  validateMcpCommand,
  withTimeout
} from './security.mjs';

function tempDir(t) {
  const dir = mkdtempSync(join(tmpdir(), 'aurora-relay-security-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

test('A.1 rejects target symlink and preserves external sentinel', t => {
  const root = tempDir(t);
  const outbox = join(root, 'outbox');
  mkdirSync(outbox);
  const sentinel = join(root, 'sentinel.txt');
  const target = join(outbox, 'probe.json');
  writeFileSync(sentinel, 'ORIGINAL\n');
  symlinkSync(sentinel, target);

  assert.throws(() => safeWriteAtomic(target, { id: 'probe' }), /symlink rejected/);
  assert.equal(readFileSync(sentinel, 'utf8'), 'ORIGINAL\n');
});

test('A.1 rejects a symlink in a parent directory', t => {
  const root = tempDir(t);
  const outside = join(root, 'outside');
  mkdirSync(outside);
  const sentinel = join(outside, 'sentinel');
  writeFileSync(sentinel, 'ORIGINAL');
  const linked = join(root, 'outbox-link');
  symlinkSync(outside, linked);

  assert.throws(() => safeWriteAtomic(join(linked, 'probe.json'), { id: 'probe' }), /symlink rejected/);
  assert.equal(readFileSync(sentinel, 'utf8'), 'ORIGINAL');
});

test('A.1 atomically writes a regular result file', t => {
  const root = tempDir(t);
  const outbox = join(root, 'outbox');
  const target = join(outbox, 'ok.json');
  safeWriteAtomic(target, { id: 'ok' });
  assert.deepEqual(JSON.parse(readFileSync(target, 'utf8')), { id: 'ok' });
});

test('A.2 rejects an inbox symlink', t => {
  const root = tempDir(t);
  const inbox = join(root, 'inbox');
  mkdirSync(inbox);
  const source = join(root, 'request.json');
  writeFileSync(source, '{"id":"req_0123456789ab"}');
  symlinkSync(source, join(inbox, 'req_0123456789ab.json'));
  assert.throws(() => readRequest(join(inbox, 'req_0123456789ab.json')), /symlink rejected/);
});

test('A.2 rejects inbox JSON larger than 64 KiB', t => {
  const root = tempDir(t);
  const file = join(root, 'large.json');
  writeFileSync(file, ' '.repeat(64 * 1024 + 1));
  assert.throws(() => readRequest(file), /request too large/);
});

test('A.2 rejects an inbox request older than 24 hours', t => {
  const root = tempDir(t);
  const file = join(root, 'expired.json');
  const old = new Date(Date.now() - 25 * 60 * 60 * 1000);
  writeFileSync(file, JSON.stringify({ protocol: 'aurora-relay/1', id: 'req_0123456789ab', action: 'PING' }));
  utimesSync(file, old, old);
  assert.throws(() => readRequest(file), /request expired/);
});

test('A.2 returns exact request SHA-256 for a valid request', t => {
  const root = tempDir(t);
  const file = join(root, 'request.json');
  const body = Buffer.from(JSON.stringify({ protocol: 'aurora-relay/1', id: 'req_0123456789ab', action: 'PING', created_at: new Date().toISOString() }));
  writeFileSync(file, body);
  const result = readRequest(file);
  assert.equal(result.requestSha256, createHash('sha256').update(body).digest('hex'));
  assert.equal(result.rawBytes, body.length);
});

test('A.3 rejects more than 100 pending JSON requests', t => {
  const root = tempDir(t);
  const inbox = join(root, 'inbox');
  mkdirSync(inbox);
  for (let i = 0; i < 101; i += 1) writeFileSync(join(inbox, \`\${i}.json\`), '{}');
  assert.throws(() => assertInboxLimit(inbox, 100), /too many pending requests/);
});

test('A.4 requires one explicit request id for publication', () => {
  assert.throws(() => parseApprovePublishArg(['node', 'relay.mjs', '--approve-publish']), /explicit request id required/);
  assert.throws(() => parseApprovePublishArg(['node', 'relay.mjs', '--approve-publish', 'bad-id']), /explicit request id required/);
  assert.equal(parseApprovePublishArg(['node', 'relay.mjs', '--approve-publish', 'req_0123456789ab']), 'req_0123456789ab');
});

test('A.5 accepts only current Node binary with matching pinned digest', async () => {
  const digest = createHash('sha256').update(readFileSync(process.execPath)).digest('hex');
  const command = await validateMcpCommand([process.execPath, 'server.cjs'], { PATH: process.env.PATH, AURORA_MCP_NODE_SHA256: digest }, process.execPath);
  assert.equal(command[0], process.execPath);
  assert.equal(command[1], 'server.cjs');
  await assert.rejects(validateMcpCommand([process.execPath, 'server.cjs'], { PATH: process.env.PATH, AURORA_MCP_NODE_SHA256: '0'.repeat(64) }, process.execPath), /hash mismatch/);
});

test('A.5 requires an explicitly configured trusted digest', async () => {
  await assert.rejects(
    validateMcpCommand([process.execPath, 'server.cjs'], { PATH: process.env.PATH }, process.execPath),
    /AURORA_MCP_NODE_SHA256/
  );
});

test('A.5 rejects a different executable even if executable', async t => {
  const root = tempDir(t);
  const fake = join(root, 'node');
  writeFileSync(fake, '#!/bin/sh\nexit 0\n');
  chmodSync(fake, 0o700);
  await assert.rejects(validateMcpCommand([fake, 'server.cjs'], { PATH: process.env.PATH, AURORA_MCP_NODE_SHA256: '0'.repeat(64) }, process.execPath), /not pinned/);
});

test('A.6 rejects a timed out MCP operation and invokes cleanup', async () => {
  let cleaned = false;
  await assert.rejects(
    withTimeout(new Promise(() => {}), 20, 'test', () => { cleaned = true; }),
    /MCP_TIMEOUT:test/
  );
  assert.equal(cleaned, true);
});

test('A.6 returns normally when operation completes before deadline', async () => {
  assert.equal(await withTimeout(Promise.resolve('ok'), 1000, 'test'), 'ok');
});
