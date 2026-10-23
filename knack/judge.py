"""Vision success judge: Nemotron 3.5 Super VL looks at camera frames and says pass/fail.

It abstains (returns success=None) when its stated confidence is under the
threshold or its answer can't be parsed. Real robots have no ground-truth
success signal, so this is the reward that transfers off the simulator.
"""
from __future__ import annotations

import base64
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .prompts import JUDGE_SYSTEM, judge_text

DEFAULT_VIEWS = ("start_front", "end_front", "end_side", "end_overhead")


@dataclass
class Verdict:
    success: bool | None
    confidence: float
    reason: str
    abstained: bool
    raw: str = ""
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def parse_verdict(text: str, threshold: float) -> Verdict:
    raw = text or ""
    obj = None
    for m in re.finditer(r"\{.*?\}", raw, flags=re.S):
        try:
            obj = json.loads(m.group(0))
            break
        except json.JSONDecodeError:
            continue
    if obj is None:
        s = re.search(r'"?success"?\s*[:=]\s*(true|false)', raw, flags=re.I)
        c = re.search(r'"?confidence"?\s*[:=]\s*([0-9.]+)', raw, flags=re.I)
        if s:
            obj = {"success": s.group(1).lower() == "true", "confidence": float(c.group(1)) if c else 0.5, "reason": ""}
    if not isinstance(obj, dict) or not isinstance(obj.get("success"), bool):
        return Verdict(None, 0.0, "unparseable judge reply", True, raw[:500], "parse")
    try:
        conf = float(obj.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    reason = str(obj.get("reason", ""))[:300]
    if conf < threshold:
        return Verdict(None, conf, reason, True, raw[:500])
    return Verdict(bool(obj["success"]), conf, reason, False, raw[:500])


def _data_url(path: Path) -> str:
    b = Path(path).read_bytes()
    mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(b).decode()}"


class VLMJudge:
    def __init__(self, llm, model: str = "super-vl", threshold: float = 0.6, views=DEFAULT_VIEWS, max_tokens: int = 1500):
        self.llm = llm
        self.model = model
        self.threshold = threshold
        self.views = tuple(views)
        self.max_tokens = max_tokens

    def judge(self, instruction: str, frames: dict, frame_dir) -> Verdict:
        frame_dir = Path(frame_dir)
        views = [v for v in self.views if v in (frames or {}) and (frame_dir / frames[v]).exists()]
        if not views:
            return Verdict(None, 0.0, "no camera frames available", True, error="no_frames")
        content = [{"type": "text", "text": judge_text(instruction, views)}]
        for v in views:
            content.append({"type": "image_url", "image_url": {"url": _data_url(frame_dir / frames[v])}})
        messages = [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": content}]
        try:
            reply = self.llm.chat("judge", self.model, messages, temperature=0.0, max_tokens=self.max_tokens)
        except Exception as e:  # network or budget: abstain, never invent a verdict
            if type(e).__name__ == "BudgetExceeded":
                raise
            return Verdict(None, 0.0, f"judge call failed: {type(e).__name__}", True, error=str(e)[:300])
        return parse_verdict(reply.text, self.threshold)
