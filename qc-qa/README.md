# QC & QA Dashboard

Interactive dashboard for the Vijaya 1 and Vijaya 2 hatcheries (2023 to 2026): Np stocking, PL sold,
DOC, TL, ADL, %SR, market area and salinity by month, year, hatchery and unit. Thai and English,
16:9 and 9:16, click-to-filter on every chart and a compare mode.

| File | Purpose |
|---|---|
| `build_qc_dashboard.py` | Reads `QC_Tank_Integrated_Report_2026.xlsx`, cleans it and writes the dashboard |
| `qc_dashboard_template.html` | Page layout, charts and Thai/English text (`/*__DATA__*/null` is replaced by the data) |

## Rebuild

```bash
python3 build_qc_dashboard.py
```

The script uses absolute paths set at the top (`BASE`, `REPORT`, `TEMPLATE`, `OUT`). Adjust `BASE` to the
machine you run it on. The report itself is produced by `qc_tank_integrated_final.py` in the hatchery
workspace and is not stored here.

## Data privacy

The built `QC_Tank_Dashboard.html` embeds tank-level production data, so it is **not** stored in this
public repository (it is git-ignored). The built file is kept in the private repo
`kittipong2021/vijaya-dashboard-private` (`dist/QC_Tank_Dashboard.html`).
