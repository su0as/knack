"""Token Factory client (OpenAI-compatible) with a per-call cost ledger.

Every call is attributed to a role (coder / summarizer / judge / probe) so the
skill card can show which model did what and what it cost.
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import ModelInfo, api_key, base_url, resolve_model


class BudgetExceeded(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


@dataclass
class Reply:
    text: str
    reasoning: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    cost: float = 0.0
    latency: float = 0.0
    model: str = ""
    tool_calls: list = field(default_factory=list)
    message: dict | None = None


class Ledger:
    """Append-only record of model calls and compute, with an optional USD budget."""

    def __init__(self, path: str | Path | None = None, budget_usd: float | None = None):
        self.path = Path(path) if path else None
        self.budget_usd = budget_usd
        self.calls: list[dict] = []
        self.compute: list[dict] = []
        self._lock = threading.Lock()

    def add_call(self, role: str, model: ModelInfo, reply: Reply, ok: bool = True, mock: bool = False):
        rec = {
            "t": round(time.time(), 2), "role": role, "alias": model.alias, "model": model.id,
            "prompt_tokens": reply.prompt_tokens, "completion_tokens": reply.completion_tokens,
            "cached_tokens": reply.cached_tokens, "usd": round(reply.cost, 6), "latency_s": round(reply.latency, 2),
            "ok": ok, "mock": mock,
        }
        with self._lock:
            self.calls.append(rec)
            self._append(rec)

    def add_compute(self, backend: str, seconds: float, usd: float, detail: dict | None = None):
        rec = {"t": round(time.time(), 2), "kind": "compute", "backend": backend, "seconds": round(seconds, 2), "usd": round(usd, 6), **(detail or {})}
        with self._lock:
            self.compute.append(rec)
            self._append(rec)

    def _append(self, rec: dict):
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")

    def llm_usd(self) -> float:
        return sum(c["usd"] for c in self.calls)

    def compute_usd(self) -> float:
        return sum(c["usd"] for c in self.compute)

    def total_usd(self) -> float:
        return self.llm_usd() + self.compute_usd()

    def check_budget(self):
        if self.budget_usd is not None and self.total_usd() >= self.budget_usd:
            raise BudgetExceeded(f"budget of ${self.budget_usd:.2f} reached (spent ${self.total_usd():.4f})")

    def by_role(self) -> dict:
        out: dict[str, dict] = {}
        for c in self.calls:
            r = out.setdefault(c["role"], {"model": c["model"], "alias": c["alias"], "calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "usd": 0.0})
            r["calls"] += 1
            r["prompt_tokens"] += c["prompt_tokens"]
            r["completion_tokens"] += c["completion_tokens"]
            r["usd"] = round(r["usd"] + c["usd"], 6)
            r["model"] = c["model"]
            r["alias"] = c["alias"]
        return out

    def summary(self) -> dict:
        return {
            "llm_usd": round(self.llm_usd(), 6),
            "compute_usd": round(self.compute_usd(), 6),
            "total_usd": round(self.total_usd(), 6),
            "calls": len(self.calls),
            "prompt_tokens": sum(c["prompt_tokens"] for c in self.calls),
            "completion_tokens": sum(c["completion_tokens"] for c in self.calls),
            "by_role": self.by_role(),
            "compute_seconds": round(sum(c["seconds"] for c in self.compute), 2),
            "mock": any(c.get("mock") for c in self.calls),
        }


_THINK = re.compile(r"<think>.*?</think>", re.S)


def strip_thinking(text: str) -> tuple[str, str]:
    """Remove <think> blocks. Returns (answer, reasoning)."""
    if not text:
        return "", ""
    reasoning = "\n".join(m.group(0)[7:-8] for m in _THINK.finditer(text))
    answer = _THINK.sub("", text)
    if "</think>" in answer:  # opening tag consumed by the chat template
        head, answer = answer.rsplit("</think>", 1)
        reasoning = (reasoning + "\n" + head).strip()
    return answer.strip(), reasoning.strip()


class LLMClient:
    """Thin wrapper over the OpenAI SDK pointed at Nebius Token Factory."""

    def __init__(self, ledger: Ledger, key: str | None = None, url: str | None = None, timeout: float = 300.0, max_retries: int = 4):
        self.ledger = ledger
        self.key = key or api_key()
        self.url = url or base_url()
        self.timeout = timeout
        self.max_retries = max_retries
        self._clients: dict[str, object] = {}
        self._model_base: dict[str, str] = {}
        if not self.key:
            raise LLMError("NEBIUS_API_KEY is not set. Put it in .env (see .env.example).")

    def _client(self, url: str):
        if url not in self._clients:
            from openai import OpenAI

            self._clients[url] = OpenAI(base_url=url, api_key=self.key, timeout=self.timeout, max_retries=0)
        return self._clients[url]

    def chat(self, role: str, model: str | ModelInfo, messages: list, *, temperature: float = 0.2, max_tokens: int = 8000,
             tools: list | None = None, extra_body: dict | None = None) -> Reply:
        m = model if isinstance(model, ModelInfo) else resolve_model(model)
        self.ledger.check_budget()
        bases = [self._model_base.get(m.id) or self.url]
        if m.region_base and m.region_base not in bases:
            bases.append(m.region_base)
        last_err = None
        for attempt in range(self.max_retries + 1):
            n404 = 0
            for b in list(bases):
                try:
                    t0 = time.time()
                    kwargs = dict(model=m.id, messages=messages, temperature=temperature, max_tokens=max_tokens)
                    if tools:
                        kwargs["tools"] = tools
                    if extra_body:
                        kwargs["extra_body"] = extra_body
                    resp = self._client(b).chat.completions.create(**kwargs)
                    self._model_base[m.id] = b
                    return self._finish(role, m, resp, time.time() - t0)
                except Exception as e:  # noqa: BLE001 - classify below
                    last_err = e
                    status = getattr(e, "status_code", None)
                    if status == 404 or "not found" in str(e).lower():
                        n404 += 1
                        continue  # try the model's regional base URL
                    if status in (400, 401, 403, 422):
                        raise LLMError(f"{m.id}: HTTP {status}: {e}") from e
                    break
            if n404 == len(bases):
                raise LLMError(f"{m.id}: model not found at {bases}. Run `knack models` to list available IDs.") from last_err
            time.sleep(min(30.0, 2.0 * (2 ** attempt)))
        raise LLMError(f"{m.id}: giving up after retries: {last_err}")

    def _finish(self, role: str, m: ModelInfo, resp, latency: float) -> Reply:
        msg = resp.choices[0].message
        raw = msg.content or ""
        text, reasoning = strip_thinking(raw)
        extra_reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None) or ""
        if extra_reasoning:
            reasoning = (str(extra_reasoning) + "\n" + reasoning).strip()
        u = resp.usage
        pt = getattr(u, "prompt_tokens", 0) or 0
        ct = getattr(u, "completion_tokens", 0) or 0
        details = getattr(u, "prompt_tokens_details", None)
        cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
        tool_calls = []
        for tc in getattr(msg, "tool_calls", None) or []:
            tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments})
        r = Reply(text=text, reasoning=reasoning, prompt_tokens=pt, completion_tokens=ct, cached_tokens=cached,
                  cost=m.cost(pt, ct, cached), latency=latency, model=m.id, tool_calls=tool_calls,
                  message=msg.model_dump() if hasattr(msg, "model_dump") else None)
        self.ledger.add_call(role, m, r)
        return r


class MockLLM:
    """Offline stand-in. `responder(role, messages) -> str`. Token counts are estimated (chars/4)."""

    def __init__(self, ledger: Ledger, responder):
        self.ledger = ledger
        self.responder = responder

    def chat(self, role: str, model, messages: list, **kw) -> Reply:
        m = model if isinstance(model, ModelInfo) else resolve_model(model)
        self.ledger.check_budget()
        text = self.responder(role, messages)
        chars = sum(len(c["text"]) if isinstance(c, dict) and "text" in c else 800 for msg in messages
                    for c in (msg["content"] if isinstance(msg["content"], list) else [{"text": msg["content"]}]))
        pt, ct = chars // 4, len(text) // 4
        r = Reply(text=text, prompt_tokens=pt, completion_tokens=ct, cost=m.cost(pt, ct), model=m.id)
        self.ledger.add_call(role, m, r, mock=True)
        return r
