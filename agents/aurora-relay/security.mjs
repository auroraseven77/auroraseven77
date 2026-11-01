import {
  accessSync,
  closeSync,
  constants,
  createReadStream,
  fstatSync,
  fsyncSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  realpathSync,
  readdirSync,
  renameSync,
  statSync,
  unlinkSync,
  writeSync
} from 'node:fs';
import { basename, dirname, join, parse, resolve, sep } from 'node:path';
import { createHash, randomBytes } from 'node:crypto';

const MAX_REQUEST_BYTES = 64 * 1024;
const MAX_REQUEST_AGE_MS = 24 * 60 * 60 * 1000;
const MAX_FUTURE_SKEW_MS = 5 * 60 * 1000;

function lstatOrNull(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    throw error;
  }
}

export function ensureSafeDirectory(directory) {
  const absolute = resolve(directory);
  const root = parse(absolute).root;
  let current = root;
  const parts = absolute.slice(root.length).split(sep).filter(Boolean);

  for (const part of parts) {
    current = join(current, part);
    let st = lstatOrNull(current);
    if (!st) {
      try {
        mkdirSync(current, { mode: 0o700 });
      } catch (error) {
        if (error?.code !== 'EEXIST') throw error;
      }
      st = lstatOrNull(current);
    }
    if (!st) throw new Error(`directory unavailable: ${current}`);
    if (st.isSymbolicLink()) throw new Error(`symlink rejected: ${current}`);
    if (!st.isDirectory()) throw new Error(`not a directory: ${current}`);
  }
  return absolute;
}

export function assertNoSymlink(path) {
  const absolute = resolve(path);
  const parent = dirname(absolute);
  ensureSafeDirectory(parent);
  const st = lstatOrNull(absolute);
  if (st?.isSymbolicLink()) throw new Error(`symlink rejected: ${absolute}`);
  if (st && !st.isFile()) throw new Error(`not a regular file: ${absolute}`);
  return st;
}

export function safeWriteAtomic(target, payload) {
  const absolute = resolve(target);
  const directory = ensureSafeDirectory(dirname(absolute));
  assertNoSymlink(absolute);

  const temporary = join(
    directory,
    `.${basename(absolute)}.${process.pid}.${randomBytes(12).toString('hex')}.tmp`
  );
  const bytes = Buffer.from(`${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  let fd;
  let created = false;

  try {
    fd = openSync(temporary, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | (constants.O_NOFOLLOW || 0), 0o600);
    created = true;
    let offset = 0;
    while (offset < bytes.length) {
      const written = writeSync(fd, bytes, offset, bytes.length - offset);
      if (written <= 0) throw new Error('atomic write made no progress');
      offset += written;
    }
    fsyncSync(fd);
    closeSync(fd);
    fd = undefined;

    // rename replaces a leaf symlink itself rather than following its target;
    // both the temporary file and parent directory are checked again here.
    ensureSafeDirectory(directory);
    assertNoSymlink(absolute);
    renameSync(temporary, absolute);

    let dirFd;
    try {
      dirFd = openSync(directory, constants.O_RDONLY);
      fsyncSync(dirFd);
    } finally {
      if (dirFd !== undefined) closeSync(dirFd);
    }
  } catch (error) {
    if (fd !== undefined) {
      try { closeSync(fd); } catch {}
    }
    if (created) {
      try { unlinkSync(temporary); } catch {}
    }
    throw error;
  }
}

export function readRequest(path, options = {}) {
  const maxBytes = options.maxBytes ?? MAX_REQUEST_BYTES;
  const maxAgeMs = options.maxAgeMs ?? MAX_REQUEST_AGE_MS;
  const absolute = resolve(path);
  assertNoSymlink(absolute);

  const noFollow = constants.O_NOFOLLOW || 0;
  const fd = openSync(absolute, constants.O_RDONLY | noFollow);
  try {
    const st = fstatSync(fd);
    if (!st.isFile()) throw new Error('inbox: not a regular file');
    if (st.size > maxBytes) throw new Error('inbox: request too large');
    const age = Date.now() - st.mtimeMs;
    if (age > maxAgeMs || age < -MAX_FUTURE_SKEW_MS) throw new Error('inbox: request expired or future-dated');

    const raw = readFileSync(fd);
    if (raw.length > maxBytes) throw new Error('inbox: request too large');
    let text;
    try {
      text = new TextDecoder('utf-8', { fatal: true }).decode(raw);
    } catch {
      throw new Error('inbox: invalid UTF-8');
    }
    let message;
    try {
      message = JSON.parse(text);
    } catch {
      throw new Error('inbox: invalid JSON');
    }
    if (message?.created_at !== undefined) {
      const createdAt = Date.parse(message.created_at);
      if (!Number.isFinite(createdAt) || Date.now() - createdAt > maxAgeMs || createdAt - Date.now() > MAX_FUTURE_SKEW_MS) {
        throw new Error('inbox: request expired or future-dated');
      }
    }
    return {
      message,
      requestSha256: createHash('sha256').update(raw).digest('hex'),
      rawBytes: raw.length
    };
  } finally {
    closeSync(fd);
  }
}

export function assertInboxLimit(inbox, maxEntries = 100) {
  ensureSafeDirectory(inbox);
  const entries = readdirSync(inbox).filter(name => name.endsWith('.json'));
  if (entries.length > maxEntries) throw new Error(`inbox: too many pending requests (${entries.length} > ${maxEntries})`);
  return entries.sort();
}

function resolveExecutable(name, pathValue = process.env.PATH || '') {
  const candidates = name.includes(sep)
    ? [resolve(name)]
    : pathValue.split(':').filter(Boolean).map(directory => join(directory, name));
  for (const candidate of candidates) {
    try {
      const real = realpathSync(candidate);
      const st = statSync(real);
      if (st.isFile()) {
        accessSync(real, constants.X_OK);
        return real;
      }
    } catch {}
  }
  throw new Error(`mcp: executable not found: ${name}`);
}

export async function validateMcpCommand(command, env = process.env, execPath = process.execPath) {
  if (!Array.isArray(command) || command.length < 1 ||
      command.some(item => typeof item !== 'string' || item.length === 0)) {
    throw new Error('MCP_COMMAND_INVALID_SHAPE');
  }
  const actualBinary = resolveExecutable(command[0], env.PATH);
  const trustedNode = realpathSync(execPath);
  if (actualBinary !== trustedNode) throw new Error('mcp: binary not pinned to current Node runtime');

  const expected = env.AURORA_MCP_NODE_SHA256;
  if (typeof expected !== 'string' || !/^[a-f0-9]{64}$/.test(expected)) {
    throw new Error('mcp: AURORA_MCP_NODE_SHA256 must contain the pinned Node SHA-256');
  }
  const hash = createHash('sha256');
  await new Promise((resolveHash, rejectHash) => {
    const stream = createReadStream(actualBinary);
    stream.on('data', chunk => hash.update(chunk));
    stream.on('error', rejectHash);
    stream.on('end', resolveHash);
  });
  const actual = hash.digest('hex');
  if (actual !== expected) throw new Error('mcp: binary hash mismatch');
  return [actualBinary, ...command.slice(1)];
}

export function parseApprovePublishArg(argv) {
  const positions = [];
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--approve-publish') positions.push(i);
  }
  if (positions.length === 0) return null;
  if (positions.length !== 1) throw new Error('publish: duplicate approval flag');
  const index = positions[0];
  const id = argv[index + 1];
  if (!id || id.startsWith('--') || !/^req_[0-9a-f]{12}$/.test(id)) {
    throw new Error('publish: explicit request id required (req_ + 12 lowercase hex characters)');
  }
  return id;
}

export async function withTimeout(promise, milliseconds, label, onTimeout = () => {}) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          try { Promise.resolve(onTimeout()).catch(() => {}); } catch {}
          reject(new Error(`MCP_TIMEOUT:${label}`));
        }, milliseconds);
      })
    ]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}
