"use strict";

const fs = require("node:fs");
const crypto = require("node:crypto");
const path = require("node:path");
const os = require("node:os");

const HOME_ROOT = fs.realpathSync(os.homedir());
const PROJECTS = Object.freeze({
  "auroraseven77": path.join(HOME_ROOT, "auroraseven77"),
  "auroraseven77-test": path.join(HOME_ROOT, "auroraseven77-test"),
  "auroraseven77-v21-validation": path.join(HOME_ROOT, "auroraseven77-v21-validation"),
  "auroraseven77-b12-audit": path.join(HOME_ROOT, "auroraseven77-b12-audit"),
  "auroraseven77-b13-repro": path.join(HOME_ROOT, "auroraseven77-b13-repro"),
  "auroraseven77-b13-energy": path.join(HOME_ROOT, "auroraseven77-b13-energy")
});
const MAX_BYTES = 48 * 1024;
const MAX_PATH_CHARS = 1024;
const ALLOWED_EXTENSIONS = new Set([".md", ".txt", ".json", ".yaml", ".yml", ".py", ".toml", ".csv"]);
const SENSITIVE = /(^|[._-])(env|pem|key|secret|credentials?|token|id_rsa|private)([._-]|$)/i;
const O_NOFOLLOW = fs.constants.O_NOFOLLOW;
// Node/libuv opens descriptors close-on-exec; O_CLOEXEC is not exposed on every Node build.

function safeError(err) {
  const code = err && typeof err.code === "string" ? err.code : "";
  if (code === "ENOENT" || code === "ENOTDIR") return "Arquivo ou diretório não encontrado.";
  if (code === "EACCES" || code === "EPERM") return "Acesso negado.";
  if (code === "ELOOP") return "Link simbólico não permitido no arquivo final.";
  if (code === "ENAMETOOLONG") return "Caminho excede o limite permitido.";
  if (code === "EMFILE" || code === "ENFILE") return "Limite de descritores temporariamente atingido.";
  return "Falha na operação; detalhes locais omitidos.";
}

function inside(root, target) {
  const rel = path.relative(root, target);
  return rel !== "" && rel !== ".." && !rel.startsWith(".." + path.sep) && !path.isAbsolute(rel);
}

function projectRoot(name) {
  if (typeof name !== "string" || !Object.prototype.hasOwnProperty.call(PROJECTS, name)) {
    throw new Error("Projeto não autorizado.");
  }
  let root;
  try { root = fs.realpathSync(PROJECTS[name]); }
  catch (e) { throw e; }
  if (path.dirname(root) !== HOME_ROOT) throw new Error("Raiz real do projeto não autorizada.");
  const st = fs.statSync(root);
  if (!st.isDirectory()) throw new Error("Projeto autorizado inválido.");
  return root;
}

function listProjects() {
  return Object.keys(PROJECTS).map(name => {
    try { projectRoot(name); return { name, exists: true }; }
    catch { return { name, exists: false }; }
  });
}

function validateRelativePath(relativePath) {
  if (typeof relativePath !== "string" || relativePath.length === 0 || relativePath.length > MAX_PATH_CHARS || relativePath.includes("\0") || relativePath.normalize("NFC") !== relativePath || path.posix.isAbsolute(relativePath) || path.win32.isAbsolute(relativePath)) {
    throw new Error("Informe um caminho relativo válido e normalizado.");
  }
  const segments = relativePath.split(/[\\/]+/);
  if (segments.some(s => !s || s === "." || s === ".." || s.startsWith("."))) throw new Error("Caminho oculto ou traversal não permitido.");
  if (segments.some(s => SENSITIVE.test(s))) throw new Error("Arquivo potencialmente sensível bloqueado.");
  const ext = path.extname(segments[segments.length - 1]).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) throw new Error("Extensão não autorizada para leitura.");
  return segments;
}

function readEvidence(project, relativePath) {
  const segments = validateRelativePath(relativePath);
  const root = projectRoot(project);
  const candidate = path.resolve(root, ...segments);
  if (!inside(root, candidate)) throw new Error("Caminho fora do projeto autorizado.");

  // Resolve expected target first, then open the original candidate path.
  // The descriptor path is checked after open to detect raced intermediate symlink changes.
  const expectedRealPath = fs.realpathSync(candidate);
  if (!inside(root, expectedRealPath)) throw new Error("Destino real fora do projeto autorizado.");
  if (!fs.existsSync("/proc/self/fd") || typeof O_NOFOLLOW !== "number") {
    throw new Error("Verificação de descritor indisponível; operação bloqueada.");
  }

  const flags = fs.constants.O_RDONLY | O_NOFOLLOW;
  const fd = fs.openSync(candidate, flags);
  try {
    const st = fs.fstatSync(fd, { bigint: true });
    if (!st.isFile()) throw new Error("Arquivo regular obrigatório.");
    if (st.size > BigInt(MAX_BYTES)) throw new Error("Arquivo excede 48 KiB.");

    let actual;
    try { actual = fs.readlinkSync(`/proc/self/fd/${fd}`); }
    catch { throw new Error("Não foi possível validar o descritor; operação bloqueada."); }
    if (actual.endsWith(" (deleted)") || actual !== expectedRealPath || !inside(root, actual)) {
      throw new Error("O destino mudou durante a abertura; operação bloqueada.");
    }

    const chunks = [];
    const chunk = Buffer.alloc(8192);
    let offset = 0;
    while (true) {
      const n = fs.readSync(fd, chunk, 0, chunk.length, offset);
      if (n === 0) break;
      offset += n;
      if (offset > MAX_BYTES) throw new Error("Arquivo excedeu 48 KiB durante a leitura.");
      chunks.push(Buffer.from(chunk.subarray(0, n)));
    }
    const after = fs.fstatSync(fd, { bigint: true });
    if (BigInt(offset) !== after.size || after.dev !== st.dev || after.ino !== st.ino || after.size > BigInt(MAX_BYTES) || after.mtimeNs !== st.mtimeNs || after.ctimeNs !== st.ctimeNs) {
      throw new Error("Arquivo alterado durante a leitura; resultado descartado.");
    }
    const bytes = Buffer.concat(chunks, offset);
    return {
      project,
      path: relativePath,
      bytes: bytes.length,
      sha256: crypto.createHash("sha256").update(bytes).digest("hex"),
      content: bytes.toString("utf8")
    };
  } finally {
    fs.closeSync(fd);
  }
}

function dispatch(name, args) {
  if (name === "aurora.list_projects") {
    if (args == null || typeof args !== "object" || Array.isArray(args) || Object.keys(args).length) throw new Error("Argumentos inválidos.");
    return listProjects();
  }
  if (name === "aurora.read_evidence") {
    if (!args || typeof args !== "object" || Array.isArray(args) || Object.keys(args).some(k => !["project", "relative_path"].includes(k)) || typeof args.project !== "string" || typeof args.relative_path !== "string") throw new Error("Argumentos inválidos.");
    return readEvidence(args.project, args.relative_path);
  }
  throw new Error("Ferramenta não autorizada.");
}

function handleCall(name, args) {
  try { return { content: [{ type: "text", text: JSON.stringify(dispatch(name, args), null, 2) }] }; }
  catch (e) { return { isError: true, content: [{ type: "text", text: JSON.stringify({ error: safeError(e) }) }] }; }
}

async function main() {
  const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
  const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
  const { ListToolsRequestSchema, CallToolRequestSchema } = require("@modelcontextprotocol/sdk/types.js");
  const server = new Server({ name: "aurora-readonly-safe", version: "1.0.1" }, { capabilities: { tools: {} } });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: [
    { name: "aurora.list_projects", description: "Lista projetos autorizados sem revelar caminhos locais.", inputSchema: { type: "object", properties: {}, additionalProperties: false } },
    { name: "aurora.read_evidence", description: "Lê evidências autorizadas de até 48 KiB e calcula SHA-256.", inputSchema: { type: "object", properties: { project: { type: "string", enum: Object.keys(PROJECTS) }, relative_path: { type: "string", maxLength: MAX_PATH_CHARS } }, required: ["project", "relative_path"], additionalProperties: false } }
  ] }));
  server.setRequestHandler(CallToolRequestSchema, async request => handleCall(request.params.name, request.params.arguments || {}));
  await server.connect(new StdioServerTransport());
}

if (require.main === module) main().catch(() => { process.stderr.write("Falha fatal no servidor MCP.\n"); process.exitCode = 1; });
module.exports = { validateRelativePath, readEvidence, listProjects, dispatch, handleCall, safeError, MAX_BYTES };
