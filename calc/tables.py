"""Shared coefficient tables and helpers from مصوبه ۴۳۷۸ (سال ۱۴۰۵)."""
from __future__ import annotations

from typing import Iterable

# Table 2 — Cf within max allowed density (تراکم مجاز)
CF_TABLE2: list[tuple[float, float, float]] = [
    # (lower_pct, upper_pct, cf)
    (0, 180, 3),
    (180, 240, 4),
    (240, 300, 5),
    (300, 360, 6),
    (360, 420, 9),
    (420, 480, 12),
    (480, 540, 16),
    (540, 600, 20),
    (600, 10_000, 24),
]

# Table 3 — excess density, north of Enghelab (regions 1–8, 22)
CF_TABLE3: list[tuple[float, float, float]] = [
    (0, 180, 6),
    (180, 240, 9),
    (240, 300, 12),
    (300, 360, 18),
    (360, 420, 20),
    (420, 480, 21),
    (480, 540, 22),
    (540, 600, 23),
    (600, 660, 24),
    (660, 720, 25),
    (720, 10_000, 26),
]

# Table 4 — excess density, south of Enghelab (regions 9–21)
CF_TABLE4: list[tuple[float, float, float]] = [
    (0, 180, 6),
    (180, 240, 9),
    (240, 300, 12),
    (300, 360, 30),
    (360, 420, 33),
    (420, 480, 36),
    (480, 540, 39),
    (540, 600, 42),
    (600, 660, 43),
    (660, 720, 44),
    (720, 10_000, 45),
]

# Table 5 — Cf by floor when density not fixed / ماده ۵
CF_TABLE5_BY_FLOOR: dict[int, float] = {
    1: 5,
    2: 5,
    3: 5,
    4: 6,
    5: 7,
}
# floors 6..19 → 8..21 ; floor ≥20 → 22
for _f in range(6, 20):
    CF_TABLE5_BY_FLOOR[_f] = _f + 2
for _f in range(20, 60):
    CF_TABLE5_BY_FLOOR[_f] = 22

# Blocks where Table-2 Cf is doubled (تبصره ذیل جدول ۱)
DOUBLE_CF_BLOCKS = {"15_6", "3_3", "3_15", "7_1"}

# K(s) by region — جدول ۶
KS_BY_REGION: dict[int, float] = {}
for r in (7, 8, 12):
    KS_BY_REGION[r] = 1.1
KS_BY_REGION[3] = 1.05
for r in (4, 6):
    KS_BY_REGION[r] = 1.00
for r in (5, 11):
    KS_BY_REGION[r] = 0.95
for r in (1, 10, 13):
    KS_BY_REGION[r] = 0.90
for r in (2, 16):
    KS_BY_REGION[r] = 0.80
KS_BY_REGION[14] = 0.75
for r in (9, 15, 18, 21):
    KS_BY_REGION[r] = 0.70
KS_BY_REGION[19] = 0.65
KS_BY_REGION[17] = 0.60
KS_BY_REGION[20] = 0.55
KS_BY_REGION[22] = 0.50

# K(ps) by floor — جدول ۷
KPS_BY_FLOOR: dict[str, float] = {
    "همکف": 5.0,
    "زیرزمین": 3.0,
    "اول": 2.5,
    "دوم": 2.25,
    "سوم_به_بالا": 1.75,
    "انباری": 1.5,
}

# Default Cs ground floor — جدول ۸ (غیر از راسته‌ها)
CS_DEFAULT = {
    ("M_S", False): 13.0,
    ("M_S", True): 17.0,  # region 12
    ("other", False): 12.0,
    ("other", True): 16.0,  # region 12
    "harim": 13.0,
}

# Cs upper floors as % of ground Cs — جدول ۹
CS_FLOOR_FACTOR: dict[str, float] = {
    "زیرزمین_اول": 0.80,
    "اول_نیم_همکف": 0.70,
    "زیرزمین_دوم_دوم": 0.50,
    "سایر": 0.40,
    "انبار": 0.60,
}

# K(m) by region — جدول ۱۰
KM_BY_REGION: dict[int, float] = {
    6: 1.35,
    3: 1.3,
    8: 1.3,
    7: 1.2,
    10: 1.2,
    1: 1.15,
    11: 1.15,
    4: 1.1,
    5: 1.0,
    12: 1.0,
    13: 1.0,
    14: 1.0,
    16: 1.0,
    18: 1.0,
    9: 0.95,
    15: 0.95,
    22: 0.9,
    19: 0.85,
    2: 0.8,
    21: 0.8,
    17: 0.8,
    20: 0.7,
}

# K(pm) by floor — جدول ۱۱
KPM_BY_FLOOR: dict[str, float] = {
    "همکف": 3.0,
    "زیرزمین": 2.5,
    "اول": 2.0,
    "دوم": 1.5,
    "سوم_به_بالا": 1.0,
    "انباری": 1.0,
}

# K(pi) by floor — جدول ۱۲
KPI_BY_FLOOR: dict[str, float] = {
    "همکف": 3.0,
    "زیرزمین": 2.5,
    "اول": 2.0,
    "دوم": 1.5,
    "سوم_به_بالا": 1.0,
    "نیم_طبقه": 0.5,
    "انباری": 1.0,
}

NORTH_ENGHELAB_REGIONS = {1, 2, 3, 4, 5, 6, 7, 8, 22}
PARKING_UNIT_M2 = 12.5


def cf_for_floor_table5(floor: int) -> float:
    if floor <= 0:
        return 5.0
    return float(CF_TABLE5_BY_FLOOR.get(floor, 22))


def split_area_by_density_brackets(
    land_area: float,
    building_area: float,
    table: list[tuple[float, float, float]],
    *,
    start_pct: float = 0.0,
    end_pct: float | None = None,
    cf_multiplier: float = 1.0,
) -> list[dict]:
    """Split زیربنا into density brackets and assign Cf."""
    if land_area <= 0 or building_area <= 0:
        return []

    total_density = (building_area / land_area) * 100.0
    if end_pct is None:
        end_pct = total_density
    end_pct = min(end_pct, total_density)
    if end_pct <= start_pct:
        return []

    remaining = building_area * ((end_pct - start_pct) / total_density) if total_density else 0
    # Better: absolute m2 for each bracket overlapping [start_pct, end_pct]
    segments: list[dict] = []
    for lower, upper, cf in table:
        overlap_lo = max(lower, start_pct)
        overlap_hi = min(upper, end_pct)
        if overlap_hi <= overlap_lo:
            continue
        area = land_area * (overlap_hi - overlap_lo) / 100.0
        if area <= 0:
            continue
        segments.append(
            {
                "lower_pct": overlap_lo,
                "upper_pct": overlap_hi,
                "area": area,
                "cf": cf * cf_multiplier,
            }
        )
    return segments


def allocate_residential_segments(
    land_area: float,
    building_area: float,
    max_allowed_density_pct: float,
    region: int,
    block_id: str,
    *,
    inefficient_fabric: bool = False,
    use_table5_floors: Iterable[tuple[float, int]] | None = None,
) -> list[dict]:
    """
    Build C(f)×S(f) segments for residential calculation.

    - تا تراکم مجاز: جدول ۲
    - مازاد: جدول ۳ (شمال انقلاب) یا ۴ (جنوب)
    - یا در حالت تبصره ۱: جدول ۵ بر اساس طبقات
    """
    cf_mult = 2.0 if block_id in DOUBLE_CF_BLOCKS else 1.0
    if inefficient_fabric:
        cf_mult *= 0.9

    if use_table5_floors:
        segs = []
        for area, floor in use_table5_floors:
            segs.append(
                {
                    "lower_pct": None,
                    "upper_pct": None,
                    "area": area,
                    "cf": cf_for_floor_table5(floor) * cf_mult,
                    "note": f"جدول ۵ — طبقه {floor}",
                }
            )
        return segs

    table_excess = (
        CF_TABLE3 if region in NORTH_ENGHELAB_REGIONS else CF_TABLE4
    )
    within = split_area_by_density_brackets(
        land_area,
        building_area,
        CF_TABLE2,
        start_pct=0.0,
        end_pct=max_allowed_density_pct,
        cf_multiplier=cf_mult,
    )
    for s in within:
        s["note"] = "جدول ۲ — در حد تراکم مجاز"

    excess = split_area_by_density_brackets(
        land_area,
        building_area,
        table_excess,
        start_pct=max_allowed_density_pct,
        end_pct=None,
        cf_multiplier=cf_mult,  # double-cf note refers to table 2; keep 1× on excess unless block flagged
    )
    # For special blocks, note says دو برابر جدول ۲ only — don't double excess tables
    if block_id in DOUBLE_CF_BLOCKS:
        for s in excess:
            s["cf"] = s["cf"] / 2.0 * (0.9 if inefficient_fabric else 1.0)
            if inefficient_fabric:
                pass
    for s in excess:
        s["note"] = (
            "جدول ۳ — مازاد (شمال انقلاب)"
            if region in NORTH_ENGHELAB_REGIONS
            else "جدول ۴ — مازاد (جنوب انقلاب)"
        )

    return within + excess


def residential_cr(n_units: int, land_area: float, useful_area: float) -> float:
    """C(r) = max(0, 10N/S - 0.2) + 0.001 × میانگین (اگر میانگین > ۲۰۰)."""
    if land_area <= 0 or n_units <= 0:
        return 0.0
    density_term = max(0.0, (10.0 * n_units / land_area) - 0.2)
    avg = useful_area / n_units
    area_term = 0.001 * avg if avg > 200 else 0.0
    return density_term + area_term


def format_rial(amount: float) -> str:
    return f"{amount:,.0f} ریال"
