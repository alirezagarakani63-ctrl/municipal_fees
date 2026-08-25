"""Extract transaction values and Table27 Cs coefficients into data/."""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import pandas as pd
import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)


def rev_persian(s: str) -> str:
    if not s:
        return ""
    return s[::-1]


def parse_block(cell: str):
    if not cell:
        return None
    cell = cell.replace("\n", " ").replace("_", " ").strip()
    m = re.search(r"(\d+)\s+(\d+(?:\(a\))?)", cell)
    if not m:
        m = re.search(r"(\d+)[_\-](\d+(?:\(a\))?)", cell)
    if not m:
        return None
    return m.group(1), m.group(2)


def parse_cs(cell: str):
    if not cell:
        return None
    cell = str(cell).replace("/", ".").replace(",", ".").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", cell)
    return float(m.group(1)) if m else None


def extract_table27(excel_blocks: list[str]) -> dict[str, float]:
    records = []
    path = os.path.join(ROOT, "Table27.pdf")
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue
                    raw = [(c or "").strip() for c in row]
                    joined = " ".join(raw)
                    if not re.search(r"\d", joined):
                        continue

                    cs = None
                    block_info = None
                    street = None

                    # Observed column order (RTL scramble): Cs, street, block, region
                    if raw and re.fullmatch(r"\d{1,2}([./]\d+)?", raw[0].replace(" ", "")):
                        val = parse_cs(raw[0])
                        if val is not None and 1 <= val <= 40:
                            cs = val

                    for c in raw:
                        if not c:
                            continue
                        bi = parse_block(c)
                        if bi:
                            block_info = bi
                            continue
                        if re.search(r"[\u0600-\u06FF]", c) and len(c) > 2:
                            street = rev_persian(c.replace("\n", " ")).strip()
                        if cs is None and re.fullmatch(
                            r"\d{1,2}([./]\d+)?", c.replace(" ", "")
                        ):
                            val = parse_cs(c)
                            if val is not None and 1 <= val <= 40:
                                cs = val

                    if block_info and cs is not None:
                        region, block = block_info
                        records.append(
                            {
                                "region": int(region),
                                "block": block,
                                "cs": cs,
                                "street": street or "",
                            }
                        )

    def normalize_key(region: int, block: str) -> str:
        candidates = [f"{region}_{block}"]
        if block.isdigit():
            candidates.append(f"{region}_{int(block):02d}")
            candidates.append(f"{region}_{int(block)}")
        for c in candidates:
            if c in excel_blocks:
                return c
        if block.isdigit():
            if region in (1, 2):
                return f"{region}_{int(block):02d}"
            return f"{region}_{int(block)}"
        return f"{region}_{block}"

    cs_map: dict[str, float] = {}
    cs_meta: dict[str, dict] = {}
    for r in records:
        key = normalize_key(r["region"], r["block"])
        prev = cs_map.get(key)
        if prev is None or r["cs"] > prev:
            cs_map[key] = r["cs"]
            cs_meta[key] = {"street": r["street"], "cs": r["cs"]}

    with open(os.path.join(DATA, "cs_table27.json"), "w", encoding="utf-8") as f:
        json.dump(cs_map, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(os.path.join(DATA, "cs_table27_meta.json"), "w", encoding="utf-8") as f:
        json.dump(cs_meta, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"Table27 records={len(records)} unique={len(cs_map)}")
    return cs_map


def extract_values() -> tuple[dict, list[str]]:
    xlsx = glob.glob(os.path.join(ROOT, "*.xlsx"))[0]
    df = pd.read_excel(xlsx, header=None)
    excel_blocks = [str(x) for x in df.iloc[1:, 1].tolist()]
    vals: dict[str, dict] = {}
    for _, row in df.iloc[1:].iterrows():
        region = int(row[0])
        block = str(row[1])
        vals[block] = {
            "region": region,
            "Pr": float(row[2]) if pd.notna(row[2]) else None,
            "Pm": float(row[3]) if pd.notna(row[3]) else None,
            "Ps": float(row[4]) if pd.notna(row[4]) else None,
            "Pr_adj": float(row[5]) if pd.notna(row[5]) else None,
            "Pm_adj": float(row[6]) if pd.notna(row[6]) else None,
            "Ps_adj": float(row[7]) if pd.notna(row[7]) else None,
        }
    with open(
        os.path.join(DATA, "transaction_values_1405.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(vals, f, ensure_ascii=False, indent=2)
    print(f"values={len(vals)}")
    return vals, excel_blocks


def main() -> int:
    _, excel_blocks = extract_values()
    cs_map = extract_table27(excel_blocks)
    print("sample 1_05", cs_map.get("1_05"), "1_16", cs_map.get("1_16"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
