"""ابنیار — سامانه محاسبه عوارض ساختمانی تهران (مصوبه ۱۴۰۵)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calc.data_loader import blocks_for_region, get_property, load_cs, load_kr, load_values
from calc.engine import (
    calc_administrative_floor,
    calc_commercial_floor,
    calc_industrial_floor,
    calc_residential,
    default_cs,
    floor_kpi,
    floor_kpm,
    floor_kps,
    lookup_km,
    lookup_ks,
)
from calc.tables import format_rial

LOGO = ROOT / "ABNiYar.jpg"

st.set_page_config(
    page_title="ابنیار | محاسبه عوارض",
    page_icon=str(LOGO) if LOGO.exists() else ":material/apartment:",
    layout="wide",
    initial_sidebar_state="expanded",
)

if LOGO.exists():
    st.logo(str(LOGO))

st.markdown(
    """
<style>
  html, body, [class*="st-"] { direction: rtl; text-align: right; }
  .stApp { background: linear-gradient(180deg, #ffffff 0%, #f3f6f9 55%, #e8eef4 100%); }
  h1, h2, h3 { color: #003050 !important; }
  div[data-testid="stMetricValue"] { color: #003050; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)


def money_metric(label: str, amount: float) -> None:
    st.metric(label, format_rial(amount))


def show_details(details: list[dict]) -> None:
    if not details:
        return
    df = pd.DataFrame(details)
    for col in df.columns:
        if df[col].dtype == float or "مبلغ" in col or "مقدار" in col or col in {
            "P(r)",
            "K(r)",
            "C(f)",
            "جزء مبلغ",
        }:
            df[col] = df[col].apply(
                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
            )
    st.dataframe(df, hide_index=True, use_container_width=True)


with st.sidebar:
    st.markdown("### ابنیار")
    st.caption("محاسبه عوارض ساختمانی تهران — سال ۱۴۰۵")
    mode = st.radio(
        "نوع محاسبه",
        [
            "مسکونی",
            "تجاری",
            "اداری",
            "صنعتی",
            "جداول پایه",
        ],
        index=0,
    )
    st.divider()
    region = st.selectbox("منطقه", list(range(1, 23)), index=0)
    block_options = blocks_for_region(region)
    block_id = st.selectbox("بلوک دارایی", block_options)
    prop = get_property(block_id)
    use_adjusted = st.toggle("استفاده از ارزش معاملاتی با ضریب تعدیل", value=True)
    st.divider()
    st.markdown("**ضرایب و ارزش‌ها**")
    st.write(f"K(r) = `{prop['kr']}`")
    if prop.get("cs_raste"):
        st.write(f"C(s) راسته (جدول ۲۷) = `{prop['cs_raste']}`")
    pr = prop["Pr"] if use_adjusted else prop["Pr_raw"]
    pm = prop["Pm"] if use_adjusted else prop["Pm_raw"]
    ps = prop["Ps"] if use_adjusted else prop["Ps_raw"]
    st.write(f"P(r) = `{pr:,.0f}`")
    st.write(f"P(m) = `{pm:,.0f}`")
    st.write(f"P(s) = `{ps:,.0f}`")

st.title("سامانه محاسبه عوارض ساختمانی")
st.caption(
    "بر اساس مصوبه ۴۳۷۸ شورای اسلامی شهر تهران — عوارض ساختمانی، ارزش‌افزوده و بهای خدمات حوزه شهرسازی از سال ۱۴۰۵"
)

if mode == "مسکونی":
    st.subheader("عوارض زیربنای مسکونی")
    c1, c2, c3 = st.columns(3)
    with c1:
        land_area = st.number_input("مساحت عرصه (م۲)", min_value=1.0, value=250.0, step=1.0)
        n_units = st.number_input("تعداد واحد مسکونی", min_value=1, value=4, step=1)
        useful_area = st.number_input("جمع مساحت مفید واحدها (م۲)", min_value=1.0, value=400.0)
    with c2:
        building_area = st.number_input("زیربنای ناخالص مسکونی (م۲)", min_value=1.0, value=500.0)
        max_density = st.number_input("حداکثر تراکم مجاز (%)", min_value=1.0, value=180.0, step=10.0)
        inefficient = st.checkbox("بافت ناکارآمد (ضریب ۰.۹)")
    with c3:
        communal = st.number_input("مشاعات فاقد کاربرد اصلی (م۲)", min_value=0.0, value=0.0)
        acquired = st.number_input("زیربنای دارای حقوق مکتسبه (م۲)", min_value=0.0, value=0.0)
        use_t5 = st.checkbox("محاسبه با جدول ۵ (طبقات / ماده ۵)")

    table5_floors = None
    if use_t5:
        st.info("مساحت هر طبقه را وارد کنید؛ ضریب C(f) از جدول ۵ تعیین می‌شود.")
        n_floors = st.number_input("تعداد طبقات دارای کاربرد", min_value=1, value=4)
        table5_floors = []
        cols = st.columns(min(4, int(n_floors)))
        for i in range(int(n_floors)):
            with cols[i % len(cols)]:
                a = st.number_input(f"مساحت طبقه {i+1}", min_value=0.0, value=100.0, key=f"t5a_{i}")
                table5_floors.append((a, i + 1))

    if st.button("محاسبه عوارض مسکونی", type="primary", icon=":material/calculate:"):
        if prop["kr"] is None:
            st.error("ضریب K(r) برای این بلوک یافت نشد.")
        else:
            result = calc_residential(
                land_area=land_area,
                n_units=int(n_units),
                useful_area=useful_area,
                building_area=building_area,
                max_allowed_density_pct=max_density,
                region=region,
                block_id=block_id,
                kr=float(prop["kr"]),
                pr=float(pr),
                inefficient_fabric=inefficient,
                communal_area=communal,
                acquired_rights_area=acquired,
                use_table5=use_t5,
                table5_floors=table5_floors,
            )
            money_metric("جمع عوارض مسکونی", result.total)
            st.caption(result.formula_note)
            show_details(result.details)

elif mode == "تجاری":
    st.subheader("عوارض زیربنای تجاری")
    c1, c2, c3 = st.columns(3)
    with c1:
        gross = st.number_input("مساحت ناخالص طبقه (م۲)", min_value=1.0, value=80.0)
        net = st.number_input("مساحت خالص تجاری (م۲)", min_value=1.0, value=60.0)
        n_units = st.number_input("تعداد واحد در طبقه", min_value=1, value=1)
    with c2:
        floor_key = st.selectbox(
            "طبقه",
            ["همکف", "زیرزمین", "اول", "دوم", "سوم_به_بالا", "انباری"],
        )
        zone = st.selectbox("پهنه", ["M_S", "other"], format_func=lambda x: "M و S" if x == "M_S" else "سایر پهنه‌ها")
        use_raste = st.toggle("راسته تجاری (جدول ۲۷)", value=bool(prop.get("cs_raste")))
    with c3:
        opening = st.number_input("طول دهنه (م)", min_value=0.0, value=3.0, step=0.1)
        height = st.number_input("ارتفاع (م)", min_value=0.0, value=4.5, step=0.1)
        cf = st.number_input("C(f) پلکانی", min_value=0.0, value=3.0)

    half = st.checkbox("نیم‌طبقه (۵۰٪ ضریب طبقه)")
    bazaar = st.checkbox("محدوده بازار تهران (Kps سه‌برابر)")
    single = st.checkbox("کل پلاک یک واحد تجاری است (ψ=۱)")
    bakery = st.checkbox("معافیت نانوایی (تبصره ۸)")
    offices_70 = st.checkbox("دفتر فروش / بازرگانی / تولیدی (۷۰٪)")

    cs_val = float(prop["cs_raste"]) if use_raste and prop.get("cs_raste") else default_cs(zone, region)
    st.write(f"C(s) همکف مورد استفاده: `{cs_val}` | K(s) = `{lookup_ks(region)}`")

    if st.button("محاسبه عوارض تجاری", type="primary", icon=":material/calculate:"):
        result = calc_commercial_floor(
            gross_area=gross,
            net_area=net,
            n_units=int(n_units),
            region=region,
            floor_key=floor_key,
            ks=lookup_ks(region),
            kps=floor_kps(floor_key, half_floor=half),
            cs_ground=cs_val,
            ps=float(ps),
            pr=float(pr),
            kr=float(prop["kr"] or 0),
            cf=cf,
            opening_length=opening,
            height=height,
            is_storage=floor_key == "انباری",
            is_bazaar=bazaar,
            single_unit_building=single,
            is_bakery_exempt=bakery,
        )
        total = result.total * (0.7 if offices_70 else 1.0)
        money_metric("جمع عوارض تجاری", total)
        st.caption(result.formula_note)
        show_details(result.details)

elif mode == "اداری":
    st.subheader("عوارض زیربنای اداری")
    c1, c2, c3 = st.columns(3)
    with c1:
        gross = st.number_input("مساحت ناخالص طبقه (م۲)", min_value=1.0, value=120.0, key="m_g")
        net = st.number_input("مساحت خالص اداری (م۲)", min_value=1.0, value=100.0, key="m_n")
        n_units = st.number_input("تعداد واحد اداری", min_value=1, value=1, key="m_u")
    with c2:
        floor_key = st.selectbox(
            "طبقه",
            ["همکف", "زیرزمین", "اول", "دوم", "سوم_به_بالا", "انباری"],
            key="m_f",
        )
        parking = st.number_input("تعداد واحد پارکینگ در طبقه", min_value=0.0, value=0.0)
        cf = st.number_input("C(f)", min_value=0.0, value=3.0, key="m_cf")
    with c3:
        half = st.checkbox("نیم‌طبقه", key="m_h")
        single = st.checkbox("کل پلاک یک واحد اداری", key="m_s")
        storage = floor_key == "انباری"

    st.write(f"K(m) = `{lookup_km(region)}`")
    if st.button("محاسبه عوارض اداری", type="primary", icon=":material/calculate:"):
        result = calc_administrative_floor(
            gross_area=gross,
            net_area=net,
            n_units=int(n_units),
            parking_units=parking,
            region=region,
            floor_key=floor_key,
            km=lookup_km(region),
            kpm=floor_kpm(floor_key, half_floor=half),
            pm=float(pm),
            pr=float(pr),
            kr=float(prop["kr"] or 0),
            cf=cf,
            is_storage=storage,
            single_unit_building=single,
        )
        money_metric("جمع عوارض اداری", result.total)
        st.caption(result.formula_note)
        show_details(result.details)

elif mode == "صنعتی":
    st.subheader("عوارض زیربنای صنعتی")
    c1, c2, c3 = st.columns(3)
    with c1:
        gross = st.number_input("مساحت ناخالص طبقه (م۲)", min_value=1.0, value=200.0, key="i_g")
        net = st.number_input("مساحت خالص صنعتی (م۲)", min_value=1.0, value=180.0, key="i_n")
        n_units = st.number_input("تعداد واحد", min_value=1, value=1, key="i_u")
    with c2:
        floor_key = st.selectbox(
            "طبقه",
            ["همکف", "زیرزمین", "اول", "دوم", "سوم_به_بالا", "نیم_طبقه", "انباری"],
            key="i_f",
        )
        parking = st.number_input("پارکینگ (واحد)", min_value=0.0, value=0.0, key="i_p")
        open_space = st.number_input("فضای باز صنعتی (م۲، فقط همکف)", min_value=0.0, value=0.0)
    with c3:
        cf = st.number_input("C(f)", min_value=0.0, value=3.0, key="i_cf")
        traditional = st.checkbox("سفره‌خانه سنتی (φ=۲۰)")
        single = st.checkbox("یک واحد در کل پلاک", key="i_s")
        tourism = st.checkbox("بوم‌گردی / اقامتگاه سنتی (۲۰٪ تعرفه صنعتی)")

    if st.button("محاسبه عوارض صنعتی", type="primary", icon=":material/calculate:"):
        result = calc_industrial_floor(
            gross_area=gross,
            net_area=net,
            n_units=int(n_units),
            parking_units=parking,
            region=region,
            floor_key=floor_key,
            kr=float(prop["kr"] or 0),
            pr=float(pr),
            kpi=floor_kpi(floor_key),
            cf=cf,
            open_space=open_space,
            is_storage=floor_key == "انباری",
            is_traditional_restaurant=traditional,
            single_unit_building=single,
        )
        total = result.total * (0.2 if tourism else 1.0)
        money_metric("جمع عوارض صنعتی", total)
        st.caption(result.formula_note)
        show_details(result.details)

else:
    st.subheader("جداول پایه داده‌ها")
    tab1, tab2, tab3 = st.tabs(["ارزش معاملاتی ۱۴۰۵", "ضریب K(r)", "ضریب C(s) جدول ۲۷"])
    with tab1:
        vals = load_values()
        rows = []
        for b, m in vals.items():
            rows.append(
                {
                    "بلوک": b,
                    "منطقه": m["region"],
                    "Pr تعدیل": m["Pr_adj"],
                    "Pm تعدیل": m["Pm_adj"],
                    "Ps تعدیل": m["Ps_adj"],
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with tab2:
        kr = load_kr()
        st.dataframe(
            pd.DataFrame([{"بلوک": k, "K(r)": v} for k, v in kr.items()]),
            hide_index=True,
            use_container_width=True,
        )
    with tab3:
        cs = load_cs()
        st.dataframe(
            pd.DataFrame([{"بلوک": k, "C(s)": v} for k, v in cs.items()]),
            hide_index=True,
            use_container_width=True,
        )

st.divider()
st.caption("ابنیار — پیاده‌سازی مصوبه عوارض ساختمانی تهران ۱۴۰۵ | صرفاً ابزار کمکی محاسباتی")
