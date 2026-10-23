"""Settings, model catalogue and .env loading.

Model IDs and per-token prices were read from the Nebius Token Factory model
catalogue on 23 Oct 2026. Prices change: check tokenfactory.nebius.com before
quoting a receipt. Run `knack models` to list what your key can see.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"


@dataclass(frozen=True)
class ModelInfo:
    alias: str
    id: str
    price_in: float  # USD per 1M input tokens
    price_out: float  # USD per 1M output tokens
    price_cached: float | None = None
    vision: bool = False
    nvidia: bool = True
    region_base: str | None = None  # base URL shown in the catalogue sample code
    context: str = ""
    note: str = ""

    def cost(self, prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0) -> float:
        cached = min(cached_tokens or 0, prompt_tokens or 0)
        fresh = (prompt_tokens or 0) - cached
        pc = self.price_cached if self.price_cached is not None else self.price_in
        return (fresh * self.price_in + cached * pc + (completion_tokens or 0) * self.price_out) / 1e6

    def to_dict(self) -> dict:
        return asdict(self)


MODELS: dict[str, ModelInfo] = {
    "ultra": ModelInfo("ultra", "nvidia/Nemotron-3-Ultra-550b-a55b", 1.00, 3.00, 0.12,
                       region_base="https://api.tokenfactory.us-central1.nebius.com/v1/", context="1M",
                       note="550B hybrid MoE, 55B active. Coder."),
    "super": ModelInfo("super", "nvidia/nemotron-3-super-120b-a12b", 0.30, 0.90, 0.06,
                       region_base="https://api.tokenfactory.us-central1.nebius.com/v1/", context="256K",
                       note="120B hybrid MoE, 12B active. Cheaper coder."),
    "nano": ModelInfo("nano", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", 0.06, 0.24,
                      region_base="https://api.tokenfactory.nebius.com/v1/", note="30B MoE, 3B active."),
    "lightning": ModelInfo("lightning", "nvidia/Nemotron-3_5-Lightning", 0.06, 0.24,
                           region_base="https://api.tokenfactory.nebius.com/v1/", context="1M",
                           note="Trace summariser."),
    "super-vl": ModelInfo("super-vl", "nvidia/Nemotron-3.5-Super-VL", 0.30, 0.90, 0.06, vision=True,
                          region_base="https://api.tokenfactory.us-north1.nebius.com/v1/", context="1M",
                          note="Vision judge."),
    "deepseek-flash": ModelInfo("deepseek-flash", "deepseek-ai/DeepSeek-V4.1-Flash", 0.30, 1.20, 0.01, vision=True,
                                nvidia=False, region_base="https://api.tokenfactory.us-north1.nebius.com/v1/",
                                note="Non-NVIDIA baseline (also on Token Factory)."),
    "kimi-k3": ModelInfo("kimi-k3", "moonshotai/Kimi-K3", 3.00, 15.00, 0.30, vision=True, nvidia=False,
                         note="Non-NVIDIA reference: the open-weight model on ASPIRE's cost chart (about 78% at about $55/task)."),
}

ROLE_DEFAULTS = {"coder": "ultra", "summarizer": "lightning", "judge": "super-vl"}


def resolve_model(name: str) -> ModelInfo:
    if name in MODELS:
        return MODELS[name]
    for m in MODELS.values():
        if m.id == name or m.id.lower() == name.lower():
            return m
    # unknown full model id: allowed, priced at 0 so receipts flag it
    return ModelInfo(alias=name.split("/")[-1], id=name, price_in=0.0, price_out=0.0, nvidia="nvidia" in name.lower(),
                     note="not in Knack's catalogue; price unknown")


def load_dotenv(path: str | os.PathLike | None = None) -> list[str]:
    """Minimal .env loader (KEY=VALUE lines). Existing env vars win. Returns keys loaded."""
    candidates = [Path(path)] if path else [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"]
    loaded = []
    for p in candidates:
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip().removeprefix("export ").strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
                loaded.append(k)
        break
    return loaded


def api_key() -> str | None:
    return os.environ.get("NEBIUS_API_KEY") or None


def base_url() -> str:
    return os.environ.get("KNACK_BASE_URL", DEFAULT_BASE_URL)


def runs_dir() -> Path:
    return Path(os.environ.get("KNACK_RUNS", "runs"))


def library_dir() -> Path:
    return Path(os.environ.get("KNACK_LIBRARY", "skills"))
