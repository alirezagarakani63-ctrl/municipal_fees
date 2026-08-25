"""Calculation engine for Tehran building fees (مصوبه ۱۴۰۵)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from calc.tables import (
    CS_DEFAULT,
    CS_FLOOR_FACTOR,
    KM_BY_REGION,
    KPM_BY_FLOOR,
    KPI_BY_FLOOR,
    KPS_BY_FLOOR,
    KS_BY_REGION,
    PARKING_UNIT_M2,
    allocate_residential_segments,
    residential_cr,
)


@dataclass
class CalcResult:
    title: str
    total: float
    details: list[dict[str, Any]] = field(default_factory=list)
    formula_note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "total": self.total,
            "details": self.details,
            "formula_note": self.formula_note,
        }


def calc_residential(
    *,
    land_area: float,
    n_units: int,
    useful_area: float,
    building_area: float,
    max_allowed_density_pct: float,
    region: int,
    block_id: str,
    kr: float,
    pr: float,
    inefficient_fabric: bool = False,
    communal_area: float = 0.0,
    acquired_rights_area: float = 0.0,
    use_table5: bool = False,
    table5_floors: list[tuple[float, int]] | None = None,
) -> CalcResult:
    """
    Tr = (1 + C(r)) × Σ [K(r) × P(r) × C(f) × S(f)]
    مشاعات / حقوق مکتسبه: با ضریب ۳ (تبصره ۲)
    """
    cr = residential_cr(n_units, land_area, useful_area)
    segments = allocate_residential_segments(
        land_area,
        building_area,
        max_allowed_density_pct,
        region,
        block_id,
        inefficient_fabric=inefficient_fabric,
        use_table5_floors=table5_floors if use_table5 else None,
    )

    details: list[dict[str, Any]] = []
    partial = 0.0
    for seg in segments:
        term = kr * pr * seg["cf"] * seg["area"]
        partial += term
        details.append(
            {
                "شرح": seg.get("note", ""),
                "مساحت (م۲)": round(seg["area"], 2),
                "C(f)": seg["cf"],
                "K(r)": kr,
                "P(r)": pr,
                "جزء مبلغ": term,
            }
        )

    # تبصره ۲: مشاعات فاقد کاربرد اصلی و حقوق مکتسبه با Cf=3
    for label, area in (
        ("مشاعات فاقد کاربرد اصلی (ضریب ۳)", communal_area),
        ("زیربنای دارای حقوق مکتسبه (ضریب ۳)", acquired_rights_area),
    ):
        if area > 0:
            term = kr * pr * 3.0 * area
            partial += term
            details.append(
                {
                    "شرح": label,
                    "مساحت (م۲)": area,
                    "C(f)": 3.0,
                    "K(r)": kr,
                    "P(r)": pr,
                    "جزء مبلغ": term,
                }
            )

    total = (1.0 + cr) * partial
    details.append(
        {
            "شرح": f"ضریب C(r) = {cr:.4f} → ضرب در (1+C(r))",
            "مساحت (م۲)": None,
            "C(f)": None,
            "K(r)": None,
            "P(r)": None,
            "جزء مبلغ": total,
        }
    )
    return CalcResult(
        title="عوارض زیربنای مسکونی",
        total=total,
        details=details,
        formula_note="Tᵣ = (1 + C(r)) × Σ [K(r) × P(r) × C(f) × S(f)]",
    )


def _psi(net_area: float, gross_area: float, single_unit_building: bool) -> float:
    if single_unit_building:
        return 1.0
    if gross_area <= 0:
        return 1.0
    return max(0.0, min(1.0, net_area / gross_area))


def calc_commercial_floor(
    *,
    gross_area: float,
    net_area: float,
    n_units: int,
    region: int,
    floor_key: str,
    ks: float,
    kps: float,
    cs_ground: float,
    ps: float,
    pr: float,
    kr: float,
    cf: float,
    opening_length: float = 3.0,
    height: float = 4.5,
    has_mezzanine: bool = False,
    is_storage: bool = False,
    is_bazaar: bool = False,
    single_unit_building: bool = False,
    is_bakery_exempt: bool = False,
) -> CalcResult:
    """
    Tsi = S × [(Ks × (Cs + (N-1)/10) × ψ × Ps) + (Kps × Cp × Ps) + (Kr × Cf × Pr)]
    """
    if is_bakery_exempt:
        return CalcResult(
            title="عوارض زیربنای تجاری (معاف نانوایی)",
            total=0.0,
            details=[{"شرح": "معافیت واحد تولید نان", "جزء مبلغ": 0.0}],
            formula_note="تبصره ۸ ماده ۲",
        )

    psi = _psi(net_area, gross_area, single_unit_building)
    if is_storage:
        unit_term = 0.0
        cs_eff = 0.0
    else:
        unit_term = max(0, n_units - 1) / 10.0
        cs_eff = cs_ground
        # apply floor factor if not ground
        if floor_key != "همکف":
            factor = CS_FLOOR_FACTOR.get(floor_key, CS_FLOOR_FACTOR["سایر"])
            if floor_key == "انبار" or is_storage:
                factor = CS_FLOOR_FACTOR["انبار"]
            cs_eff = cs_ground * factor
        cs_eff = min(cs_eff + unit_term, 4.0) if not is_storage else 0.0
        # When combining: max of (Cs+(N-1)/10) = 4
        combined = min(cs_ground * (
            1.0 if floor_key == "همکف" else CS_FLOOR_FACTOR.get(floor_key, 0.4)
        ) + unit_term, 4.0)
        cs_eff = 0.0 if is_storage else combined

    # Cp from opening & height excess
    l0 = 3.0
    h0 = 6.5 if has_mezzanine else 4.5
    if is_storage:
        h0 = 3.0
    cp = max(0.0, (opening_length - l0) / 10.0) + max(0.0, (height - h0) / 10.0)
    cp = min(cp, 4.0)

    kps_eff = kps * 3.0 if is_bazaar else kps

    term1 = ks * cs_eff * psi * ps
    term2 = kps_eff * cp * ps
    term3 = kr * cf * pr
    unit_price = term1 + term2 + term3
    total = gross_area * unit_price

    details = [
        {"شرح": "ψ (نسبت خالص به ناخالص)", "مقدار": round(psi, 4)},
        {"شرح": "Cs مؤثر + (N-1)/10 (سقف ۴)", "مقدار": round(cs_eff, 4)},
        {"شرح": "Cp (دهنه و ارتفاع، سقف ۴)", "مقدار": round(cp, 4)},
        {"شرح": "Ks × Cs_eff × ψ × Ps", "مقدار": term1},
        {"شرح": "Kps × Cp × Ps", "مقدار": term2},
        {"شرح": "Kr × Cf × Pr", "مقدار": term3},
        {"شرح": "مبلغ طبقه", "مقدار": total},
    ]
    return CalcResult(
        title=f"عوارض زیربنای تجاری — {floor_key}",
        total=total,
        details=details,
        formula_note="Tsᵢ = S × [(Ks×(Cs+(N-1)/10)×ψ×Ps) + (Kps×Cp×Ps) + (Kr×Cf×Pr)]",
    )


def calc_administrative_floor(
    *,
    gross_area: float,
    net_area: float,
    n_units: int,
    parking_units: float,
    region: int,
    floor_key: str,
    km: float,
    kpm: float,
    pm: float,
    pr: float,
    kr: float,
    cf: float,
    is_storage: bool = False,
    single_unit_building: bool = False,
) -> CalcResult:
    """
    Tmi = S × [1 + (N-1)/30] × [Km × Cm × ψ × Pm + Kpm × Pm + Kr × Cf × Pr]
    Cm = 2.5 (اداری) یا 0.6 (انباری)
    (N-1)/30 سقف ۱.۵ برای اداری و ۰ برای انباری
    """
    s_eff = max(0.0, gross_area - parking_units * PARKING_UNIT_M2)
    psi = _psi(net_area, s_eff if s_eff > 0 else gross_area, single_unit_building)
    cm = 0.6 if is_storage else 2.5
    unit_factor = 0.0 if is_storage else min(1.5, max(0, n_units - 1) / 30.0)

    inner = (km * cm * psi * pm) + (kpm * pm) + (kr * cf * pr)
    total = s_eff * (1.0 + unit_factor) * inner

    details = [
        {"شرح": "مساحت مؤثر (پس از کسر پارکینگ)", "مقدار": s_eff},
        {"شرح": "ψ", "مقدار": round(psi, 4)},
        {"شرح": "Cm", "مقدار": cm},
        {"شرح": "(N-1)/30 (سقف ۱.۵)", "مقدار": unit_factor},
        {"شرح": "مبلغ طبقه", "مقدار": total},
    ]
    return CalcResult(
        title=f"عوارض زیربنای اداری — {floor_key}",
        total=total,
        details=details,
        formula_note="Tmᵢ = S×[1+(N-1)/30]×[Km×Cm×ψ×Pm + Kpm×Pm + Kr×Cf×Pr]",
    )


def calc_industrial_floor(
    *,
    gross_area: float,
    net_area: float,
    n_units: int,
    parking_units: float,
    region: int,
    floor_key: str,
    kr: float,
    pr: float,
    kpi: float,
    cf: float,
    open_space: float = 0.0,
    is_storage: bool = False,
    is_traditional_restaurant: bool = False,
    single_unit_building: bool = False,
) -> CalcResult:
    """
    Ti = S × [1+(N-1)/20] × [Kr × φ × Ci × ψ × Pr + Kip × Pr + Kr × Cf × Pr]
       + open_space × (Pr/4)   (فقط همکف)
    """
    s_eff = max(0.0, gross_area - parking_units * PARKING_UNIT_M2)
    psi = _psi(net_area, s_eff if s_eff > 0 else gross_area, single_unit_building)
    phi = 20.0 if is_traditional_restaurant else 1.0

    # صنعتی: Ci=1 / انباری=0.5 — مناطق ۹، ۱۸، ۲۱ و حریم: صنعتی=2 / انباری=1
    if region in (9, 18, 21):
        ci = 1.0 if is_storage else 2.0
    else:
        ci = 0.5 if is_storage else 1.0

    unit_factor = 0.0 if is_storage else min(1.5, max(0, n_units - 1) / 20.0)
    inner = (kr * phi * ci * psi * pr) + (kpi * pr) + (kr * cf * pr)
    total = s_eff * (1.0 + unit_factor) * inner

    if floor_key == "همکف" and open_space > 0:
        total += open_space * (pr / 4.0)

    details = [
        {"شرح": "مساحت مؤثر", "مقدار": s_eff},
        {"شرح": "φ", "مقدار": phi},
        {"شرح": "Ci", "مقدار": ci},
        {"شرح": "فضای باز × Pr/4", "مقدار": open_space * (pr / 4.0) if floor_key == "همکف" else 0},
        {"شرح": "مبلغ", "مقدار": total},
    ]
    return CalcResult(
        title=f"عوارض زیربنای صنعتی — {floor_key}",
        total=total,
        details=details,
        formula_note="فرمول بند ج ماده ۲ (صنعتی)",
    )


def lookup_ks(region: int) -> float:
    return KS_BY_REGION.get(region, 0.7)


def lookup_km(region: int) -> float:
    return KM_BY_REGION.get(region, 1.0)


def default_cs(zone: str, region: int, in_harim: bool = False) -> float:
    if in_harim:
        return CS_DEFAULT["harim"]
    key = ("M_S" if zone == "M_S" else "other", region == 12)
    return CS_DEFAULT[key]


def floor_kps(floor_key: str, half_floor: bool = False) -> float:
    base = KPS_BY_FLOOR.get(floor_key, 1.75)
    return base * 0.5 if half_floor else base


def floor_kpm(floor_key: str, half_floor: bool = False) -> float:
    base = KPM_BY_FLOOR.get(floor_key, 1.0)
    return base * 0.5 if half_floor else base


def floor_kpi(floor_key: str) -> float:
    return KPI_BY_FLOOR.get(floor_key, 1.0)
