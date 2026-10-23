"""Small statistics helpers (no scipy)."""
from __future__ import annotations

import math


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval. Returns (p_hat, lo, hi)."""
    if n <= 0:
        return 0.0, 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def fmt_ci(k: int, n: int) -> str:
    p, lo, hi = wilson(k, n)
    return f"{k}/{n} = {p:.0%} (95% CI {lo:.0%}-{hi:.0%})"


def judge_metrics(pairs: list[tuple]) -> dict:
    """pairs: (gt: bool, pred: bool|None). None = abstained."""
    n = len(pairs)
    decided = [(g, p) for g, p in pairs if p is not None]
    tp = sum(1 for g, p in decided if g and p)
    tn = sum(1 for g, p in decided if not g and not p)
    fp = sum(1 for g, p in decided if not g and p)
    fn = sum(1 for g, p in decided if g and not p)
    m = len(decided)
    acc = (tp + tn) / m if m else None
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    # Cohen's kappa on decided items
    kappa = None
    if m:
        po = (tp + tn) / m
        pg = (tp + fn) / m
        pp = (tp + fp) / m
        pe = pg * pp + (1 - pg) * (1 - pp)
        kappa = (po - pe) / (1 - pe) if pe < 1 else None
    return {
        "n": n, "decided": m, "abstained": n - m, "abstain_rate": (n - m) / n if n else None,
        "accuracy": acc, "precision": prec, "recall": rec, "kappa": kappa,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "false_success_rate": fp / (fp + tn) if (fp + tn) else None,
    }
