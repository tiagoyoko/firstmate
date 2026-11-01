// Shared portable/native conformance probe. The native mode uses the installed
// omp loader's prepared-factory rebinding and its real identity-bearing runner.
import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const repo = process.env.FM_ROOT_OVERRIDE;
const home = process.env.FM_HOME;
const paths = ["fm-primary-turnend-guard.ts", "fm-primary-omp-watch.ts"].map(name => `${repo}/.omp/extensions/${name}`);
const markerNames = [".omp-turnend-extension-loaded", ".omp-watch-extension-loaded"];
const native = process.env.FM_OMP_NATIVE_PACKAGE;
const modules = native ? await import(`${native}/src/extensibility/extensions/loader.ts`) : null;
const Runner = native ? (await import(`${native}/src/extensibility/extensions/runner.ts`)).ExtensionRunner : null;
assert.equal(existsSync(`${home}/state`), false, "the primary must start without a state directory");
const prepared = modules ? await modules.loadExtensions(paths, repo) : await Promise.all(paths.map(path => import(pathToFileURL(path).href)));
if (modules) assert.deepEqual(prepared.errors, []);
assert.equal(existsSync(`${home}/state`), false, "loading extensions cannot create primary state");
let first = true;
async function bind(kind, id, source = prepared) {
  const ctx = { agent: { kind, id, name: kind, depth: 0, ...(kind === "sub" ? { parentId: "main" } : {}) }, sessionManager: { getCwd: () => repo, getSessionId: () => id } };
  const sent = [];
  if (modules) {
    const loaded = first ? source : await modules.bindPreparedExtensions(source.preparedExtensions, repo);
    first = false;
    assert.deepEqual(loaded.errors, []);
    loaded.runtime.sendUserMessage = (content, options) => sent.push({ content, options });
    const runner = new Runner(loaded.extensions, loaded.runtime, repo, ctx.sessionManager, {}, undefined, undefined, undefined, undefined, ctx.agent);
    const errors = [];
    runner.onError(error => errors.push(error));
    const tool = loaded.extensions.flatMap(ext => [...ext.tools.values()]).find(tool => tool.definition.name === "fm_watch_arm_omp").definition;
    return {
      sent, errors,
      emit: event => event.type === "before_agent_start" ? runner.emitBeforeAgentStart(event.prompt, [], []) : runner.emit(event),
      arm: () => tool.execute("arm", {}, undefined, undefined, runner.createContext()),
    };
  }
  const handlers = new Map();
  let tool;
  for (const mod of source) mod.default({
    on(event, handler) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
    registerCommand() {}, registerTool(value) { tool = value; }, sendMessage() {},
    sendUserMessage(content, options) { sent.push({ content, options }); },
  });
  return {
    sent, errors: [],
    async emit(event) {
      let result;
      for (const handler of handlers.get(event.type) ?? []) result = (await handler(event, ctx)) ?? result;
      return result;
    },
    arm: () => tool.execute("arm", {}, undefined, undefined, ctx),
  };
}
async function until(predicate, label) {
  for (let i = 0; i < 300; i++) {
    if (predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  throw new Error(`timed out: ${label}`);
}
const rows = () => existsSync(`${home}/state/arms`) ? readFileSync(`${home}/state/arms`, "utf8").trim().split("\n") : [];
const earlyChild = await bind("sub", "early-depth-zero-child");
await earlyChild.emit({ type: "session_start" });
await earlyChild.emit({ type: "session_compact" });
assert.equal(await earlyChild.emit({ type: "before_agent_start", prompt: "early child" }), undefined);
assert.equal(await earlyChild.emit({ type: "session_stop", stop_hook_active: false }), undefined);
assert.equal((await earlyChild.arm()).details.ok, false, "a subagent cannot initialize primary supervision");
await earlyChild.emit({ type: "session_shutdown" });
assert.equal(existsSync(`${home}/state`), false, "subagent binding and lifecycle cannot create primary state");
const dormant = await bind("main", "dormant-primary");
const main = await bind("main", "main");
assert.equal(existsSync(`${home}/state`), false, "factory bind cannot create primary state or publish ownership");
await main.emit({ type: "session_start" });
for (const name of markerNames) {
  const marker = readFileSync(`${home}/state/${name}`, "utf8").trim().split("\n");
  assert.match(marker[0], /^sha256:[a-f0-9]{64}$/, `${name} must publish the loaded extension version`);
  assert.equal(marker[1], String(process.pid), `${name} must publish the primary pid`);
}
assert.equal(rows().length, 0, "marker publication cannot arm without the primary lock");
writeFileSync(`${home}/state/.lock`, `${process.pid}\n`);
assert.equal((await main.arm()).details.ok, true, "the activated primary can arm after acquiring its lock");
await until(() => rows().length === 1, "primary arm");
console.log("ok - fresh primary publishes both markers in TURNEND-before-WATCH order without factory or subagent state");
assert.equal((await dormant.arm()).details.ok, false, "a dormant prior factory cannot claim a newer primary from a late tool");
await dormant.emit({ type: "session_shutdown" });
assert.equal((await main.arm()).details.ok, true, "a dormant prior factory shutdown cannot retire the active primary");
const child = await bind("sub", "depth-zero-child");
assert.equal((await main.arm()).details.ok, true, "subagent bind must not displace main");
await child.emit({ type: "session_start" });
await child.emit({ type: "session_compact" });
assert.equal(await child.emit({ type: "before_agent_start", prompt: "child" }), undefined);
assert.equal(await child.emit({ type: "session_stop", stop_hook_active: false }), undefined);
assert.equal((await child.arm()).details.ok, false, "subagent tool cannot arm the primary");
await child.emit({ type: "session_shutdown" });
assert.equal((await main.arm()).details.ok, true, "subagent shutdown must preserve main");
assert.equal(rows().length, 1, "subagent must not start another arm");
const digest = await main.emit({ type: "before_agent_start", prompt: "main" });
assert.ok(JSON.stringify(digest).includes("OMP DIGEST source=startup"), "subagent lifecycle must not cancel primary startup delivery");
assert.equal(readFileSync(`${home}/state/startups`, "utf8").trim(), "startup", "only the primary runs startup");
assert.equal(existsSync(`${home}/state/guards`), false, "subagent must not run the primary stop guard");
console.log("ok - primary ownership and startup survive depth-zero subagent bind/start/compact/stop/shutdown");
writeFileSync(`${home}/state/trigger`, "signal: primary-native-lifecycle\n");
await until(() => main.sent.length === 1 && rows().length === 2, "wake plus successor");
assert.ok(main.sent[0].content.includes("FIRSTMATE WATCHER WAKE: signal: primary-native-lifecycle"));
assert.equal(main.sent[0].options.deliverAs, "followUp");
assert.deepEqual(child.sent, []);
await main.emit({ type: "before_agent_start", prompt: main.sent[0].content });
await main.emit({ type: "session_shutdown" });
assert.equal((await main.arm()).details.ok, false, "real shutdown cannot be rearmed by a late tool");
const replacement = await bind("main", "replacement");
await replacement.emit({ type: "session_start" });
await until(() => rows().length === 3, "replacement arm");
await main.emit({ type: "session_shutdown" });
assert.equal((await main.arm()).details.ok, false, "stale primary tool cannot steal the replacement");
assert.equal((await replacement.arm()).details.ok, true, "stale shutdown must preserve replacement");
await replacement.emit({ type: "session_shutdown" });
await replacement.emit({ type: "session_start" });
await until(() => rows().length === 4, "same-instance replacement arm");
assert.equal((await replacement.arm()).details.ok, true);
// Distinct home modules share process-wide coordinators, never their ownership.
const otherHome = `${home}-other`;
process.env.FM_HOME = otherHome;
const otherPaths = paths.map(path => path.replace(repo, `${repo}-other`));
const otherPrepared = modules
  ? await modules.loadExtensions(otherPaths, `${repo}-other`)
  : await Promise.all(otherPaths.map(path => import(pathToFileURL(path).href)));
const other = await bind("main", "other-home", otherPrepared);
writeFileSync(`${otherHome}/state/.lock`, `${process.pid}\n`);
await other.emit({ type: "session_start" });
await until(() => existsSync(`${otherHome}/state/arms`), "separate-home arm");
process.env.FM_HOME = home;
assert.equal((await replacement.arm()).details.ok, true, "separate-home primary cannot displace this home");
writeFileSync(`${otherHome}/state/trigger`, "signal: separate-home-only\n");
await until(() => other.sent.length === 1, "separate-home wake");
assert.ok(other.sent[0].content.includes("signal: separate-home-only"));
assert.equal(replacement.sent.length, 0, "separate-home wake cannot reach the replacement");
await other.emit({ type: "before_agent_start", prompt: other.sent[0].content });
await other.emit({ type: "session_shutdown" });
assert.equal((await replacement.arm()).details.ok, true, "separate-home shutdown cannot stop this home");
assert.deepEqual(other.errors, []);
console.log("ok - separate homes preserve independent ownership, delivery and shutdown");
await replacement.emit({ type: "session_shutdown" });
assert.equal((await replacement.arm()).details.ok, false);
const foreignMarkers = markerNames.map(name => `foreign-owner-${name}\n1\n`);
markerNames.forEach((name, index) => writeFileSync(`${home}/state/${name}`, foreignMarkers[index]));
writeFileSync(`${home}/state/.lock`, "1\n");
const foreign = await bind("main", "foreign-lock-primary");
await foreign.emit({ type: "session_start" });
assert.equal((await foreign.arm()).details.ok, false, "a primary cannot arm under a foreign lock");
assert.deepEqual(markerNames.map(name => readFileSync(`${home}/state/${name}`, "utf8")), foreignMarkers, "a foreign lock must prevent either marker from being replaced");
assert.equal(readFileSync(`${home}/state/.lock`, "utf8"), "1\n");
await foreign.emit({ type: "session_shutdown" });
assert.deepEqual(foreign.errors, []);
assert.deepEqual(earlyChild.errors, []);
assert.deepEqual(main.errors, []);
assert.deepEqual(dormant.errors, []);
assert.deepEqual(child.errors, []);
assert.deepEqual(replacement.errors, []);
console.log("ok - wake delivery, successor continuity, primary replacement and stale-shutdown rejection");
process.exit(0);
