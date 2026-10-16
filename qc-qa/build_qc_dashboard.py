#!/usr/bin/env python3
"""Build the interactive QC dashboard (single HTML file).

Reads  Output/QC/QC_Tank_Integrated_Report_2026.xlsx   (sheets Vijaya1, Vijaya2)
Uses   Working/qc_dashboard_template.html               (layout, charts, TH/EN text)
Writes Output/Dashboard/QC_Tank_Dashboard.html          (data embedded, works offline)

Data model handed to the page:
  batches : one entry per tank batch  (Hatchery, Unit, Crop, Tank, Np stocking date)
            -> stocking-side values (Np, density, TL at PL1 / DOC10 / DOC13 ...)
  rows    : one entry per selling/packing event, pointing at its batch
            -> packing-side values (PL sold, DOC, TL, ADL, salinity, area ...)
Keeping the two apart stops Np from being counted twice when a tank sells to
several customers, and lets every filter act on the right level.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

BASE = "/Volumes/Work/Documents:Claude_Work:Input"
REPORT = f"{BASE}/Output/QC/QC_Tank_Integrated_Report_2026.xlsx"
TEMPLATE = f"{BASE}/Working/qc_dashboard_template.html"
OUT = f"{BASE}/Output/Dashboard/QC_Tank_Dashboard.html"

DOC_MAX = 40          # DOC at packing above this is a typo in the source (max seen: 93)
SAL_MIN, SAL_MAX = 0, 40
HATCH_CODE = {"Vijaya1": "VJ1", "Vijaya2": "VJ2"}
SAL_BINS = [("≤5", 0, 5.5), ("6", 5.5, 6.5), ("7", 6.5, 7.5), ("8", 7.5, 8.5),
            ("9–10", 8.5, 10.5), ("11–12", 10.5, 12.5), ("13–15", 12.5, 15.5), (">15", 15.5, 99)]


def num(s):
    return pd.to_numeric(s, errors="coerce")


def first_valid(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan


def norm_area(x):
    if pd.isna(x):
        return None
    t = re.sub(r"\s+", " ", str(x)).strip().strip(".,").upper()
    return t or None


def region_of(code):
    if pd.isna(code):
        return None
    m = re.match(r"[A-Za-z]+", str(code).strip())
    return m.group(0).upper() if m else None


def salinity_of(x):
    """'15' / 15.0 / '15,12' -> mean of the numbers found (ppt)."""
    if pd.isna(x):
        return np.nan
    vals = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", str(x))]
    vals = [v for v in vals if SAL_MIN <= v <= SAL_MAX]
    return float(np.mean(vals)) if vals else np.nan


def norm_brooder(x):
    if pd.isna(x) or str(x).strip() in ("", "-"):
        return None
    t = str(x).strip()
    return {"SYAQUA": "SyAqua", "KONABAY": "Konabay"}.get(t.upper(), t)


def pct(series):
    """Fractions (0.09) -> percent (9). Series already in percent are left alone."""
    s = num(series)
    return s * 100 if s.dropna().median() <= 1.5 else s


def sal_bin(v):
    if pd.isna(v):
        return None
    for i, (_, lo, hi) in enumerate(SAL_BINS):
        if lo <= v < hi:
            return i
    return None


def load():
    frames = []
    for sh in ("Vijaya1", "Vijaya2"):
        d = pd.read_excel(REPORT, sheet_name=sh)
        d["Tank No."] = d["Tank No."].astype(str)
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def build():
    df = load()
    df["Np stocking date"] = pd.to_datetime(df["Np stocking date"], errors="coerce")
    df["Selling date"] = pd.to_datetime(df["Selling date"], errors="coerce")
    df = df.dropna(subset=["Np stocking date"]).copy()
    df["h"] = df["Hatchery"].map(HATCH_CODE)
    df["unit_key"] = df["h"] + "·" + df["Unit"].astype(str)
    key = ["Hatchery", "Unit", "Crop", "Tank No.", "Np stocking date"]
    df["bid"] = df.groupby(key, sort=False).ngroup()

    # ── batches ────────────────────────────────────────────────────────────
    g = df.groupby("bid", sort=True)
    b = pd.DataFrame({
        "h": g["h"].first(), "unit_key": g["unit_key"].first(),
        "crop": g["Crop"].first(), "tank": g["Tank No."].first(),
        "sd": g["Np stocking date"].first(),
        "vol": g["Total volume (Ton.)"].agg(first_valid),
        "np": g["Np stocking bill"].agg(first_valid),
        "npa": g["Np stocking Actual"].agg(first_valid),
        "dens": g["Bill density"].agg(first_valid),
        "br": g["Brooder source"].agg(first_valid).map(norm_brooder),
        "tl1": g["TL PL1 (mm)"].agg(first_valid),
        "tl10": g["DOC 10 TL (mm)"].agg(first_valid),
        "tl13": g["DOC 13 TL (mm)"].agg(first_valid),
    })
    b["cv13"] = pct(g["%CV DOC13"].agg(first_valid))
    for c in ("vol", "np", "npa", "dens", "tl1", "tl10", "tl13"):
        b[c] = num(b[c])

    # ── selling rows ───────────────────────────────────────────────────────
    r = df[df["Selling date"].notna()].copy()
    r["doc"] = num(r["DOC packing"]).where(lambda s: s <= DOC_MAX)
    r["pl"] = num(r["Total PL Selling (mil.)"])
    r["prod"] = num(r["Total Production (Mil.)"])
    r["tl"] = num(r["TL-Packing"])
    r["cv"] = pct(r["%CV-Packing"])
    r["wt"] = num(r["Weight (pcs/g)-packing"])
    r["st"] = pct(r["%ST Packing"])
    r["adl"] = num(r["ADL (mm)"])
    r["sal"] = r["Packing Salinity"].map(salinity_of)
    r["area"] = r["Market Area"].map(norm_area)
    r["region"] = r["Market code"].map(region_of)
    r["product"] = r["Type of Product"].astype(str).str.strip().replace({"nan": None})

    # batch-level survival from ALL its rows -> flag impossible values (>100 %)
    pl_by_b = r.groupby("bid")["pl"].sum(min_count=1)
    b["sr"] = (pl_by_b.reindex(b.index) / b["np"] * 100).where(b["np"] > 0)
    b["flag"] = (b["sr"] > 100).fillna(False)

    # ── dictionary-code the categories ─────────────────────────────────────
    units = sorted(b["unit_key"].unique())
    brooders = sorted(x for x in b["br"].dropna().unique())
    products = [p for p in ("PL4", "PL12", "Flight") if p in set(r["product"].dropna())]
    regions = r["region"].value_counts().index.tolist()
    areas = r["area"].value_counts().index.tolist()
    idx = lambda lst: {v: i for i, v in enumerate(lst)}
    iu, ib, ip, ig, ia = idx(units), idx(brooders), idx(products), idx(regions), idx(areas)

    def rnd(v, n=3):
        return None if pd.isna(v) else round(float(v), n)

    batches = []
    for bid, x in b.iterrows():
        batches.append([
            0 if x.h == "VJ1" else 1, iu[x.unit_key], int(x.crop), x.tank,
            x.sd.strftime("%Y-%m-%d"),
            rnd(x.vol, 1), rnd(x.np), rnd(x.npa), rnd(x.dens, 1),
            ib.get(x.br, -1), rnd(x.tl1, 2), rnd(x.tl10, 2), rnd(x.tl13, 2),
            rnd(x.cv13, 2), rnd(x.sr, 1), 1 if x.flag else 0,
        ])
    rows = []
    for _, x in r.iterrows():
        rows.append([
            int(x.bid), x["Selling date"].strftime("%Y-%m-%d"),
            ip.get(x["product"], -1), ia.get(x["area"], -1), ig.get(x["region"], -1),
            rnd(x.sal, 1), sal_bin(x.sal) if pd.notna(x.sal) else -1,
            rnd(x.pl, 4), rnd(x["prod"], 4), rnd(x.doc, 0), rnd(x.tl, 2),
            rnd(x.cv, 2), rnd(x.wt, 0), rnd(x.st, 1), rnd(x.adl, 3),
        ])

    data = {
        "units": units, "brooders": brooders, "products": products,
        "regions": regions, "areas": areas, "salBins": [s[0] for s in SAL_BINS],
        "batchCols": ["h", "u", "crop", "tank", "sd", "vol", "np", "npa", "dens", "br",
                      "tl1", "tl10", "tl13", "cv13", "sr", "flag"],
        "rowCols": ["b", "ld", "pr", "ar", "rg", "sal", "sb", "pl", "prod", "doc", "tl",
                    "cv", "wt", "st", "adl"],
        "batches": batches, "rows": rows,
        "built": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "source": os.path.basename(REPORT),
    }
    stats = {
        "batches": len(batches), "rows": len(rows),
        "flag_sr_gt_100": int(b["flag"].sum()),
        "doc_dropped": int((num(r["DOC packing"]) > DOC_MAX).sum()),
        "salinity_filled_pct": round(float(r["sal"].notna().mean() * 100), 1),
        "area_filled_pct": round(float(r["area"].notna().mean() * 100), 1),
        "areas": len(areas), "regions": regions, "brooders": brooders,
        "products": products, "units": units,
        "st_median": rnd(r["st"].median(), 1), "cv_median": rnd(r["cv"].median(), 2),
    }
    return data, stats


def main():
    data, stats = build()
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if not os.path.exists(TEMPLATE):
        print("template not found yet -> data check only")
        return
    html = open(TEMPLATE, encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    if "/*__DATA__*/" not in html:
        sys.exit("placeholder /*__DATA__*/ missing in template")
    html = html.replace("/*__DATA__*/null", payload)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"✓ wrote {OUT}  ({os.path.getsize(OUT) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
