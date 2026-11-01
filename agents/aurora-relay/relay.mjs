import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const VERSION = "0.4.0";
const BRANCH = "agent/aurora-relay";
const RELAY_PATH = "agents/aurora-relay";
const PROJECT_TOOL = "aurora.list_projects";
const READ_TOOL = "aurora.read_evidence";
const READ_PROJECT = "auroraseven77";
const READ_PATH = "README.md";
const ALLOWED_PROJECTS = Object.freeze([
  "auroraseven77",
  "auroraseven77-test",
  "auroraseven77-v21-validation",
  "auroraseven77-b12-audit",
  "auroraseven77-b13-repro",
  "auroraseven77-b13-energy"
]);
const ALLOWED_ACTIONS = new Set(["PING", "MCP_DISCOVERY", "MCP_LIST_PROJECTS", "MCP_READ_EVIDENCE_METADATA", "CAPABILITIES"]);

function argValue(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
}
function hasFlag(name) {
  return process.argv.includes(name);
}
function git(repo, args) {
  const r = spawnSync("git", args, { cwd: repo, encoding: "utf8", timeout: 30000 });
  if (r.error || r.status !== 0) {
    const detail = (r.stderr || r.error?.message || "git command failed").trim().slice(0, 400);
    throw new Error(`GIT_FAILURE: ${detail}`);
  }
  return (r.stdout || "").trim();
}
function safeId(value) {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(value);
}
function validEnvelope(message) {
  if (!message || typeof message !== "object" || Array.isArray(message)) return false;
  const allowedKeys = new Set(["protocol", "id", "action", "created_at"]);
  if (Object.keys(message).some(key => !allowedKeys.has(key))) return false;
  if (message.protocol !== "aurora-relay/1" || !safeId(message.id) || typeof message.action !== "string") return false;
  if (message.created_at !== undefined &&
      (typeof message.created_at !== "string" || !Number.isFinite(Date.parse(message.created_at)))) return false;
  return true;
}
function writeResult(outbox, id, action, result) {
  const body = {
    protocol: "aurora-relay/1",
    id,
    action,
    agent_version: VERSION,
    created_at: new Date().toISOString(),
    result
  };
  const canonical = JSON.stringify(body);
  const payload = { ...body, sha256: createHash("sha256").update(canonical).digest("hex") };
  const target = join(outbox, `${id}.json`);
  const temp = `${target}.tmp`;
  writeFileSync(temp, JSON.stringify(payload, null, 2) + "\n", { mode: 0o600 });
  renameSync(temp, target);
}
function readMcpCommand() {
  const raw = process.env.AURORA_MCP_COMMAND;
  if (!raw) throw new Error("MCP_COMMAND_NOT_CONFIGURED");
  let parsed;
  try { parsed = JSON.parse(raw); } catch { throw new Error("MCP_COMMAND_INVALID_JSON"); }
  if (!Array.isArray(parsed) || parsed.length < 1 ||
      parsed.some(x => typeof x !== "string" || x.length === 0)) {
    throw new Error("MCP_COMMAND_INVALID_SHAPE");
  }
  return parsed;
}
function createMcpClient() {
  const command = readMcpCommand();
  const env = {};
  for (const key of ["PATH", "HOME", "PREFIX", "TMPDIR", "LANG", "LC_ALL", "ANDROID_ROOT", "ANDROID_DATA"]) {
    if (typeof process.env[key] === "string") env[key] = process.env[key];
  }
  const transport = new StdioClientTransport({
    command: command[0],
    args: command.slice(1),
    env
  });
  const client = new Client(
    { name: "aurora-relay-agent", version: VERSION },
    { capabilities: {} }
  );
  return { client, transport };
}
async function discoverMcpTools() {
  const { client, transport } = createMcpClient();
  try {
    await client.connect(transport);
    const response = await client.listTools();
    const names = (response.tools || []).map(tool => tool?.name).filter(Boolean).sort();
    return {
      status: "MCP_DISCOVERY_OK",
      tool_count: names.length,
      tool_names: names
    };
  } finally {
    await client.close().catch(() => {});
  }
}
async function readEvidenceMetadata() {
  const { client, transport } = createMcpClient();
  try {
    await client.connect(transport);
    const discovery = await client.listTools();
    const tool = (discovery.tools || []).find(item => item?.name === READ_TOOL);
    if (!tool) return { status: "MCP_TOOL_UNAVAILABLE", tool_name: READ_TOOL };

    const schema = tool.inputSchema;
    const properties = schema?.properties;
    if (!schema || schema.type !== "object" || !properties ||
        Array.isArray(properties) ||
        Object.keys(properties).sort().join(",") !== "project,relative_path" ||
        properties.project?.type !== "string" ||
        !Array.isArray(properties.project.enum) ||
        !properties.project.enum.includes(READ_PROJECT) ||
        properties.relative_path?.type !== "string" ||
        properties.relative_path.maxLength !== 1024 ||
        !Array.isArray(schema.required) ||
        schema.required.slice().sort().join(",") !== "project,relative_path" ||
        schema.additionalProperties !== false) {
      return { status: "MCP_TOOL_SCHEMA_REJECTED", tool_name: READ_TOOL };
    }

    const response = await client.callTool({
      name: READ_TOOL,
      arguments: { project: READ_PROJECT, relative_path: READ_PATH }
    });
    if (response?.isError === true) {
      return { status: "MCP_TOOL_CALL_FAILED", tool_name: READ_TOOL };
    }
    const block = (response?.content || []).find(item => item?.type === "text" && typeof item.text === "string");
    if (!block) return { status: "MCP_TOOL_RESPONSE_INVALID" };

    let record;
    try { record = JSON.parse(block.text); }
    catch { return { status: "MCP_TOOL_RESPONSE_INVALID" }; }
    if (!record || typeof record !== "object" || Array.isArray(record) ||
        Object.keys(record).sort().join(",") !== "bytes,content,path,project,sha256" ||
        record.project !== READ_PROJECT || record.path !== READ_PATH ||
        !Number.isSafeInteger(record.bytes) || record.bytes < 0 || record.bytes > 48 * 1024 ||
        typeof record.content !== "string" ||
        !/^[a-f0-9]{64}$/.test(record.sha256)) {
      return { status: "MCP_EVIDENCE_RESPONSE_REJECTED" };
    }
    const bytes = Buffer.from(record.content, "utf8");
    const actualHash = createHash("sha256").update(bytes).digest("hex");
    if (bytes.length !== record.bytes || actualHash !== record.sha256) {
      return { status: "MCP_EVIDENCE_INTEGRITY_FAILED" };
    }
    return {
      status: "MCP_READ_EVIDENCE_METADATA_OK",
      project: READ_PROJECT,
      path: READ_PATH,
      bytes: record.bytes,
      sha256: record.sha256,
      content_returned: false
    };
  } finally {
    await client.close().catch(() => {});
  }
}

async function listMcpProjects() {
  const { client, transport } = createMcpClient();
  try {
    await client.connect(transport);
    const discovery = await client.listTools();
    const tool = (discovery.tools || []).find(item => item?.name === PROJECT_TOOL);
    if (!tool) return { status: "MCP_TOOL_UNAVAILABLE", tool_name: PROJECT_TOOL };

    const schema = tool.inputSchema;
    if (!schema || schema.type !== "object" || !schema.properties ||
        Array.isArray(schema.properties) || Object.keys(schema.properties).length !== 0 ||
        schema.additionalProperties !== false) {
      return { status: "MCP_TOOL_SCHEMA_REJECTED", tool_name: PROJECT_TOOL };
    }

    const response = await client.callTool({ name: PROJECT_TOOL, arguments: {} });
    if (response?.isError === true) {
      return { status: "MCP_TOOL_CALL_FAILED", tool_name: PROJECT_TOOL };
    }
    const block = (response?.content || []).find(item => item?.type === "text" && typeof item.text === "string");
    if (!block) return { status: "MCP_TOOL_RESPONSE_INVALID" };

    let rows;
    try { rows = JSON.parse(block.text); }
    catch { return { status: "MCP_TOOL_RESPONSE_INVALID" }; }
    if (!Array.isArray(rows) || rows.length !== ALLOWED_PROJECTS.length) {
      return { status: "MCP_PROJECT_LIST_REJECTED" };
    }

    const observed = new Map();
    for (const row of rows) {
      if (!row || typeof row !== "object" || Array.isArray(row) ||
          Object.keys(row).sort().join(",") !== "exists,name" ||
          typeof row.name !== "string" || typeof row.exists !== "boolean" ||
          !ALLOWED_PROJECTS.includes(row.name) || observed.has(row.name)) {
        return { status: "MCP_PROJECT_LIST_REJECTED" };
      }
      observed.set(row.name, row.exists);
    }
    if (observed.size !== ALLOWED_PROJECTS.length) {
      return { status: "MCP_PROJECT_LIST_REJECTED" };
    }

    return {
      status: "MCP_LIST_PROJECTS_OK",
      project_count: ALLOWED_PROJECTS.length,
      projects: ALLOWED_PROJECTS.map(name => ({ name, exists: observed.get(name) }))
    };
  } finally {
    await client.close().catch(() => {});
  }
}

function getCapabilities() {
  return {
    status: "CAPABILITIES_OK",
    relay_version: VERSION,
    generated_at: new Date().toISOString(),
    actions: [
      { name: "PING", safe: true, approval: false, implemented: true },
      { name: "MCP_DISCOVERY", safe: true, approval: false, implemented: true },
      { name: "MCP_LIST_PROJECTS", safe: true, approval: false, implemented: true },
      { name: "MCP_READ_EVIDENCE_METADATA", safe: true, approval: false, implemented: true },
      { name: "CAPABILITIES", safe: true, approval: false, implemented: true }
    ],
    deferred_actions: [
      { name: "FS_READ", implemented: false },
      { name: "FS_WRITE", implemented: false, approval: true },
      { name: "FS_DELETE", implemented: false, approval: true },
      { name: "TASK_CREATE", implemented: false, approval: true },
      { name: "TASK_UPDATE", implemented: false, approval: true },
      { name: "TASK_EXECUTE", implemented: false, approval: true }
    ],
    workspace: null,
    projects_authorized: ALLOWED_PROJECTS.slice(),
    execution_policy: "READ_ONLY",
    approval_policy: "NO_MUTATING_ACTIONS_ENABLED"
  };
}

async function main() {
  const repoArg = argValue("--repo");
  if (!repoArg) throw new Error("USAGE: node relay.mjs --repo /path/to/clone [--approve-publish]");
  const repo = resolve(repoArg);
  if (!existsSync(join(repo, ".git"))) throw new Error("REPO_NOT_FOUND: --repo must be a Git working tree");

  const root = git(repo, ["rev-parse", "--show-toplevel"]);
  if (resolve(root) !== repo) throw new Error("REPO_PATH_MISMATCH");
  const currentBranch = git(repo, ["branch", "--show-current"]);
  if (currentBranch !== BRANCH) throw new Error(`WRONG_BRANCH: expected ${BRANCH}, got ${currentBranch || "(detached)"}`);

  const dirtyLines = git(repo, ["status", "--porcelain"]).split("\n").filter(Boolean);
  const unexpectedChanges = dirtyLines.filter(line => !line.startsWith("?? agents/aurora-relay/outbox/"));
  if (unexpectedChanges.length) {
    throw new Error("DIRTY_WORKTREE: only untracked relay outbox results are allowed; no changes were made");
  }

  git(repo, ["fetch", "--quiet", "origin", BRANCH]);
  git(repo, ["merge", "--ff-only", `origin/${BRANCH}`]);

  const inbox = join(repo, RELAY_PATH, "inbox");
  const outbox = join(repo, RELAY_PATH, "outbox");
  mkdirSync(inbox, { recursive: true });
  mkdirSync(outbox, { recursive: true });

  const files = readdirSync(inbox).filter(name => name.endsWith(".json")).sort();
  let processed = 0;

  for (const file of files) {
    const path = join(inbox, file);
    let message;
    try { message = JSON.parse(readFileSync(path, "utf8")); }
    catch { console.error(`SKIP_INVALID_JSON=${file}`); continue; }

    const id = message?.id;
    if (!validEnvelope(message) || file !== `${id}.json`) {
      console.error(`SKIP_INVALID_ENVELOPE=${file}`);
      continue;
    }
    const resultPath = join(outbox, `${id}.json`);
    if (existsSync(resultPath)) continue;

    let result;
    if (!ALLOWED_ACTIONS.has(message.action)) {
      result = { status: "REJECTED_UNSUPPORTED_ACTION" };
    } else if (message.action === "PING") {
      result = { status: "PONG", transport: "git-mailbox" };
    } else if (message.action === "MCP_DISCOVERY") {
      try {
        result = await discoverMcpTools();
      } catch (error) {
        const code = typeof error?.message === "string" &&
          /^[A-Z0-9_:-]{1,80}$/.test(error.message)
          ? error.message : "MCP_CONNECTION_FAILED";
        result = { status: "MCP_DISCOVERY_FAILED", error_code: code };
      }
    } else if (message.action === "CAPABILITIES") {\n      result = getCapabilities();\n    } else if (message.action === "MCP_LIST_PROJECTS") 
      try {
        result = await listMcpProjects();
      } catch (error) {
        const code = typeof error?.message === "string" &&
          /^[A-Z0-9_:-]{1,80}$/.test(error.message)
          ? error.message : "MCP_LIST_PROJECTS_FAILED";
        result = { status: "MCP_LIST_PROJECTS_FAILED", error_code: code };
      }
    } else {
      try {
        result = await readEvidenceMetadata();
      } catch (error) {
        const code = typeof error?.message === "string" &&
          /^[A-Z0-9_:-]{1,80}$/.test(error.message)
          ? error.message : "MCP_READ_EVIDENCE_FAILED";
        result = { status: "MCP_READ_EVIDENCE_FAILED", error_code: code };
      }
    }

    writeResult(outbox, id, message.action, result);
    processed += 1;
  }

  const outboxFiles = readdirSync(outbox).filter(name => name.endsWith(".json"));
  if (!hasFlag("--approve-publish")) {
    if (outboxFiles.length > 0) {
      console.log(`LOCAL_RESULTS_READY=${outboxFiles.length}`);
      console.log("PUBLISH_NOT_APPROVED: inspect outbox/ then rerun with --approve-publish");
    } else {
      console.log("NO_PENDING_REQUESTS");
    }
    return;
  }

  git(repo, ["add", "--", `${RELAY_PATH}/outbox`]);
  const staged = git(repo, ["diff", "--cached", "--name-only"]);
  if (staged) {
    git(repo, ["-c", "user.name=Aurora Relay Agent", "-c", "user.email=aurora-relay@users.noreply.github.com",
      "commit", "-m", `aurora-relay: publish ${outboxFiles.length} result(s)`]);
    git(repo, ["push", "origin", BRANCH]);
    console.log(`PUBLISHED=${outboxFiles.length}`);
  } else {
    console.log(processed > 0 ? "NO_NEW_RESULTS_TO_PUBLISH" : "NO_LOCAL_RESULTS_TO_PUBLISH");
  }
}

main().catch(error => {
  console.error(`AURORA_RELAY_ERROR=${String(error?.message || "UNKNOWN").slice(0, 500)}`);
  process.exitCode = 1;
});
