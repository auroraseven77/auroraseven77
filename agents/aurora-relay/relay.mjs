import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const VERSION = "0.1.0";
const BRANCH = "agent/aurora-relay";
const RELAY_PATH = "agents/aurora-relay";
const ALLOWED_ACTIONS = new Set(["PING", "MCP_DISCOVERY"]);

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
async function discoverMcpTools() {
  const command = readMcpCommand();
  const env = Object.fromEntries(
    Object.entries(process.env).filter(([, value]) => typeof value === "string")
  );
  const transport = new StdioClientTransport({
    command: command[0],
    args: command.slice(1),
    env
  });
  const client = new Client(
    { name: "aurora-relay-agent", version: VERSION },
    { capabilities: {} }
  );
  try {
    await client.connect(transport);
    const response = await client.listTools();
    const names = (response.tools || []).map(tool => tool.name).filter(Boolean).sort();
    return {
      status: "MCP_DISCOVERY_OK",
      tool_count: names.length,
      tool_names: names
    };
  } finally {
    await client.close().catch(() => {});
  }
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
    if (!safeId(id) || file !== `${id}.json` || message?.protocol !== "aurora-relay/1") {
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
    } else {
      try {
        result = await discoverMcpTools();
      } catch (error) {
        const code = typeof error?.message === "string" &&
          /^[A-Z0-9_:-]{1,80}$/.test(error.message)
          ? error.message : "MCP_CONNECTION_FAILED";
        result = { status: "MCP_DISCOVERY_FAILED", error_code: code };
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
