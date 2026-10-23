// Knack console. Vanilla JS, polls the run directory through the local server.
const $ = (id) => document.getElementById(id);
const S = { tasks: [], run: null, state: null, view: "code", codeRound: null, codeCache: {}, pollT: null };
const ROLE_LABEL = { coder: "CODER", summarizer: "TRACES", judge: "JUDGE" };

async function getJSON(url, opts) {
  const r = await fetch(url, Object.assign({ cache: "no-store" }, opts || {}));
  return r.json();
}
async function getText(url) {
  const r = await fetch(url, { cache: "no-store" });
  return r.ok ? r.text() : "";
}
const pct = (x) => (x === null || x === undefined ? "-" : Math.round(x * 100) + "%");
const usd = (x) => "$" + (x || 0).toFixed(4);
const fileURL = (rel) => `/api/runs/${encodeURI(S.run)}/file/${rel}`;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function init() {
  S.tasks = await getJSON("/api/tasks");
  const sel = $("task");
  sel.innerHTML = S.tasks.map((t) => `<option value="${t.id}">${esc(t.title)} (${t.id})</option>`).join("");
  sel.onchange = () => { $("instruction").value = S.tasks.find((t) => t.id === sel.value).instruction; syncReward(); };
  sel.onchange();
  $("instruction").oninput = syncReward;
  $("go").onclick = start;
  document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => { S.view = b.dataset.view; document.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("on", x === b)); renderCode(true); }));
  $("runpick").onchange = (e) => selectRun(e.target.value);
  if (!localStorage.getItem("knack-onboarded")) $("onboard").classList.remove("hidden");
  $("obok").onclick = () => { localStorage.setItem("knack-onboarded", "1"); $("onboard").classList.add("hidden"); };
  await refreshRuns(true);
  setInterval(refreshRuns, 4000);
}

function syncReward() {
  const t = S.tasks.find((x) => x.id === $("task").value);
  const custom = $("instruction").value.trim() !== t.instruction;
  const rw = $("reward");
  if (custom) { rw.value = "vlm"; rw.disabled = true; rw.title = "Custom wording has no simulator check, so the vision judge is the reward."; }
  else { rw.disabled = false; rw.title = ""; }
}

async function refreshRuns(selectNewest) {
  const runs = await getJSON("/api/runs");
  const pick = $("runpick");
  const cur = S.run;
  pick.innerHTML = '<option value="">previous runs...</option>' + runs.map((r) =>
    `<option value="${esc(r.run_id)}">${esc(r.run_id)}  [${esc(r.status)}${r.eval_p != null ? " " + pct(r.eval_p) : ""}]${r.mock ? " mock" : ""}</option>`).join("");
  if (cur) pick.value = cur;
  if (selectNewest && runs.length && !cur) selectRun(runs[0].run_id);
}

async function start() {
  const body = {
    task: $("task").value, instruction: $("instruction").value, coder: $("coder").value, reward: $("reward").value,
    n: +$("n").value, rounds: +$("rounds").value, eval: 50, budget: 1.0, mock: $("mock").checked,
  };
  $("go").disabled = true;
  try {
    const r = await getJSON("/api/learn", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (r.error) { alert(r.error); return; }
    S.codeCache = {};
    setTimeout(() => selectRun(r.run_id), 800);
  } finally { setTimeout(() => ($("go").disabled = false), 1500); }
}

function selectRun(id) {
  if (!id) return;
  S.run = id; S.state = null; S.codeRound = null; S.codeCache = {};
  $("runpick").value = id;
  clearInterval(S.pollT);
  poll();
  S.pollT = setInterval(poll, 1000);
}

async function poll() {
  if (!S.run) return;
  let st;
  try { st = await getJSON(`/api/runs/${encodeURI(S.run)}/state`); } catch (e) { return; }
  if (!st || st.error) { $("phase").textContent = "waiting for the run to start..."; return; }
  S.state = st;
  render();
  if (st.status !== "running" && st.status !== "starting") { clearInterval(S.pollT); S.pollT = setInterval(poll, 5000); }
}

function render() {
  const st = S.state;
  $("roundlbl").textContent = st.phase && st.phase.startsWith("evaluating") ? "EVAL" : `ROUND ${st.round || 0}/${st.rounds_max}`;
  $("phase").textContent = `${st.phase || ""}  ${st.elapsed ? Math.round(st.elapsed) + " s" : ""}${st.mock ? "  (mock run)" : ""}${st.error ? "  " + st.error : ""}`;
  $("spend").textContent = usd((st.cost || {}).total_usd);
  renderChips(st);
  renderTiles(st);
  renderTimeline(st);
  const last = (st.rounds || []).slice(-1)[0];
  const lastWithSummary = (st.rounds || []).filter((r) => r.summary).slice(-1)[0];
  $("summary").textContent = lastWithSummary ? lastWithSummary.summary : (last ? "No failures to analyse in the latest round." : "No failures analysed yet.");
  renderCode(false);
  renderCard(st);
}

function renderChips(st) {
  const by = ((st.cost || {}).by_role) || {};
  $("chips").innerHTML = Object.entries(st.models || {}).map(([role, m]) => {
    const u = by[role] || {};
    const tok = (u.prompt_tokens || 0) + (u.completion_tokens || 0);
    return `<div class="chip" title="${esc(m.id)}"><span class="role ${m.nvidia ? "" : "nv0"}">${ROLE_LABEL[role] || role.toUpperCase()}</span>${esc(m.id.split("/").pop())}<span class="meta">${tok.toLocaleString()} tok ${usd(u.usd)}</span></div>`;
  }).join("");
}

function tileState(e, reward) {
  if (e.status !== "done") return e.status === "running" ? "running" : "queued";
  if (reward === "vlm" && e.judge) return e.judge.abstained ? "unk" : (e.judge.success ? "ok" : "bad");
  if (reward === "self") return e.self_report ? "ok" : "bad";
  return e.success_gt ? "ok" : "bad";
}

function renderTiles(st) {
  const el = $("tiles");
  const eps = st.episodes || [];
  const ts = Date.now();
  if (el.dataset.key !== S.run + ":" + eps.map((e) => e.seed).join(",")) {
    el.dataset.key = S.run + ":" + eps.map((e) => e.seed).join(",");
    el.innerHTML = eps.map((e) => `<div class="tile" id="t${e.seed}"><img alt="seed ${e.seed}"><div class="bar"><span>seed ${e.seed}</span><span class="b"></span></div><div class="err"></div></div>`).join("");
  }
  for (const e of eps) {
    const t = document.getElementById("t" + e.seed);
    if (!t) continue;
    const s = tileState(e, st.reward);
    t.className = "tile " + (s === "queued" ? "" : s);
    const img = t.querySelector("img");
    const frames = e.frames || {};
    let src = null;
    if (e.status === "done" && frames.end_front) src = fileURL(`${e.dir}/${frames.end_front}`);
    else if (e.status === "running") src = fileURL(`${e.dir}/live.jpg`) + "?t=" + ts;
    if (src && img.dataset.src !== src) { img.dataset.src = src; img.src = src; }
    const label = { running: '<span class="badge run">RUN</span>', queued: '<span class="badge q">QUEUED</span>', ok: '<span class="badge ok">PASS</span>', bad: '<span class="badge bad">FAIL</span>', unk: '<span class="badge unk">UNSURE</span>' }[s];
    let judge = "";
    if (e.judge) judge = `<span class="judge">VL ${e.judge.abstained ? "?" : e.judge.success ? "pass" : "fail"} ${(e.judge.confidence || 0).toFixed(2)}</span> `;
    if (st.reward !== "gt" && e.success_gt !== null && e.success_gt !== undefined && e.status === "done") judge += `<span class="judge">GT ${e.success_gt ? "pass" : "fail"}</span> `;
    t.querySelector(".b").innerHTML = judge + label;
    t.querySelector(".err").textContent = e.error || (e.judge && e.judge.reason) || "";
  }
}

function renderTimeline(st) {
  const rs = st.rounds || [];
  const bars = [];
  for (let i = 1; i <= st.rounds_max; i++) {
    const r = rs.find((x) => x.round === i);
    const cur = !r && st.round === i;
    const h = r ? Math.max(2, r.success * 100) : 0;
    bars.push(`<div class="tl ${cur ? "cur" : ""}" title="${r ? `${r.k}/${r.n} | ${usd(r.usd_cum)} so far` : ""}"><div class="col" style="height:${cur ? 4 : h}%"></div><em>R${i}<br>${r ? r.k + "/" + r.n : cur ? "..." : ""}</em></div>`);
  }
  if (st.eval) bars.push(`<div class="tl" title="held-out"><div class="col" style="height:${Math.max(2, st.eval.p * 100)}%;background:#fff"></div><em>HELD<br>${st.eval.k}/${st.eval.n}</em></div>`);
  $("timeline").innerHTML = bars.join("");
}

async function renderCode(force) {
  const st = S.state;
  if (!st) return;
  const k = st.round || 0;
  if (!k) { $("code").textContent = "(the coder has not produced code yet)"; return; }
  const key = `${S.run}:${k}:${S.view}`;
  if (!force && S.codeRound === key) return;
  S.codeRound = key;
  const rel = S.view === "code" ? `round_${k}/skill.py` : S.view === "diff" ? `round_${k}/diff.patch` : `round_${k}/notes.md`;
  if (!S.codeCache[key]) S.codeCache[key] = await getText(fileURL(rel));
  const txt = S.codeCache[key] || "(empty)";
  if (S.view === "diff") {
    $("code").innerHTML = txt.split("\n").map((l) => {
      const c = l.startsWith("+") && !l.startsWith("+++") ? "add" : l.startsWith("-") && !l.startsWith("---") ? "del" : l.startsWith("@@") ? "hunk" : "";
      return `<span class="${c}">${esc(l)}</span>`;
    }).join("\n");
  } else $("code").textContent = txt;
}

async function renderCard(st) {
  const box = $("card");
  if (st.status === "running" || st.status === "starting" || !st.card) { box.classList.add("hidden"); return; }
  if (box.dataset.run === S.run) return;
  const card = await getJSON(`/api/runs/${encodeURI(S.run)}/card`);
  if (!card || card.error) return;
  box.dataset.run = S.run;
  box.classList.remove("hidden");
  const ev = card.eval || {};
  $("evsrc").textContent = ev.source === "vlm" ? "(vision judge)" : "(ground truth)";
  $("evp").textContent = pct(ev.p);
  $("evk").textContent = ev.n ? `${ev.k}/${ev.n} held-out layouts, Wilson 95% CI ${pct(ev.lo)} to ${pct(ev.hi)}` : "not evaluated";
  $("ciband").style.left = (ev.lo || 0) * 100 + "%";
  $("ciband").style.width = ((ev.hi || 0) - (ev.lo || 0)) * 100 + "%";
  $("cidot").style.left = (ev.p || 0) * 100 + "%";
  const j = ev.judge;
  $("evextra").innerHTML = `${card.practice_episodes} practice episodes, best version from round ${card.best_round}. Safety layer: ${ev.halts || 0} halts, ${ev.safety_clamps || 0} clamps.` +
    (j && j.decided ? `<br>Vision judge vs ground truth: accuracy ${pct(j.accuracy)}, abstained ${pct(j.abstain_rate)}, false-success ${pct(j.false_success_rate)}.` : "") +
    (card.mock ? "<br><b>Mock run:</b> canned code, estimated tokens." : "");
  const rows = Object.entries(card.models).map(([role, m]) => `<tr><td>${ROLE_LABEL[role] || role}</td><td>${esc(m.id.split("/").pop())}</td><td class="r">${(m.prompt_tokens + m.completion_tokens).toLocaleString()}</td><td class="r">${usd(m.usd)}</td></tr>`);
  const rc = card.receipt;
  rows.push(`<tr><td>COMPUTE</td><td>${esc(rc.backend)}</td><td class="r">${Math.round(rc.compute_seconds || 0)} s</td><td class="r">${usd(rc.compute_usd)}</td></tr>`);
  rows.push(`<tr><th>TOTAL</th><th></th><th class="r">${(rc.prompt_tokens + rc.completion_tokens).toLocaleString()}</th><th class="r">${usd(rc.total_usd)}</th></tr>`);
  $("receipt").innerHTML = `<tr><th>role</th><th>model</th><th class="r">tokens</th><th class="r">USD</th></tr>` + rows.join("");
  $("gallery").innerHTML = (ev.failures || []).map((f) => `<figure>${f.frame ? `<img src="${fileURL(f.frame)}">` : ""}<figcaption>seed ${f.seed}<br>${esc(f.error || JSON.stringify(f.metrics || {}))}</figcaption></figure>`).join("") || '<span class="muted">No held-out failures.</span>';
  $("cardlink").href = fileURL("card.html");
}

init();
