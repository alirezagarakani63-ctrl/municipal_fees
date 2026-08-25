"""Data loading helpers."""
from __future__ import annotations

import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


@lru_cache(maxsize=1)
def load_kr() -> dict[str, float]:
    with open(os.path.join(DATA, "kr_coefficients.json"), encoding="utf-8") as f:
        return {k: float(v) for k, v in json.load(f).items()}


@lru_cache(maxsize=1)
def load_values() -> dict[str, dict]:
    with open(
        os.path.join(DATA, "transaction_values_1405.json"), encoding="utf-8"
    ) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_cs() -> dict[str, float]:
    path = os.path.join(DATA, "cs_table27.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {k: float(v) for k, v in json.load(f).items()}


@lru_cache(maxsize=1)
def load_cs_meta() -> dict[str, dict]:
    path = os.path.join(DATA, "cs_table27_meta.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def blocks_for_region(region: int) -> list[str]:
    vals = load_values()
    return sorted(
        [b for b, meta in vals.items() if int(meta["region"]) == region],
        key=lambda x: x,
    )


def get_property(block_id: str) -> dict:
    vals = load_values()
    kr = load_kr()
    cs = load_cs()
    meta = vals[block_id]
    return {
        "block": block_id,
        "region": int(meta["region"]),
        "kr": kr.get(block_id),
        "cs_raste": cs.get(block_id),
        "Pr": meta["Pr_adj"] or meta["Pr"],
        "Pm": meta["Pm_adj"] or meta["Pm"],
        "Ps": meta["Ps_adj"] or meta["Ps"],
        "Pr_raw": meta["Pr"],
        "Pm_raw": meta["Pm"],
        "Ps_raw": meta["Ps"],
    }
