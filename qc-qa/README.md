# QC & QA Dashboard

Interactive dashboard for the Vijaya 1 and Vijaya 2 hatcheries (2023 to 2026): Np stocking, PL sold,
DOC, TL, ADL, %SR, market area and salinity by month, year, hatchery and unit. Thai and English (opens in English each visit),
layout adapts automatically to landscape or portrait screens, click-to-filter on every chart and a compare mode.

| File | Purpose |
|---|---|
| `build_qc_dashboard.py` | Reads `QC_Tank_Integrated_Report_2026.xlsx`, cleans it and writes the dashboard |
| `qc_dashboard_template.html` | Page layout, charts and Thai/English text (`/*__DATA__*/null` is replaced by the data) |

## Rebuild

```bash
mkdir -p data && cp /path/to/QC_Tank_Integrated_Report_2026.xlsx data/
python3 build_qc_dashboard.py
```

Defaults: report `data/QC_Tank_Integrated_Report_2026.xlsx`, output `dist/QC_Tank_Dashboard.html`. Override with the
`QC_REPORT`, `QC_TEMPLATE` and `QC_OUT` environment variables. Every chart and value is computed from the report, so a
new report gives a new dashboard.

Automatic rebuild: the private repo `kittipong2021/vijaya-dashboard-private` runs this script in GitHub Actions
whenever `data/QC_Tank_Integrated_Report_2026.xlsx` is pushed (see its `.github/workflows/build-qc.yml`).

## Data privacy

The built `QC_Tank_Dashboard.html` embeds tank-level production data, so it is **not** stored in this
public repository (it is git-ignored). The built file is kept in the private repo
`kittipong2021/vijaya-dashboard-private` (`dist/QC_Tank_Dashboard.html`).
