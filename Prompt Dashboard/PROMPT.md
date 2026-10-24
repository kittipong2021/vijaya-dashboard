# Prompt — QC Dashboard for a hatchery branch

Copy everything inside the box into Claude, attach the data workbook (and this folder if Claude Code is used).

```text
You are building an executive "QC Dashboard" for shrimp hatchery <BRANCH NAME> (hatcheries: <CODE1>, <CODE2>).

DATA
The workbook <FILE> has one sheet per hatchery (<SHEET1>, <SHEET2>) in the 36-column "QC Tank Integrated Report" layout described in
"Prompt Dashboard/DATA_FORM.md". One row = one invoice (a tank sold to a customer). Tank = hatchery + unit + crop + tank no. + Np stocking date.
First check the data: count tanks and invoices, list customer-name spellings that look like the same person (ask me to confirm before merging),
and report blanks / impossible values (DOC outside 0–50, %SR > 100). Do not silently drop rows.

BUILD
1. Run  python3 "Prompt Dashboard/tools/build_dashboard.py" config.json <FILE> dashboard.html customer_name_map.json
   (config.json = title, hatchery sheets and codes). If anything fails, fix the tool rather than rewriting the dashboard.
2. Open the result in a headless browser at 1440 px and 420 px wide; confirm there are no JS errors and that Tanks, Np stocked, PL sold and %SR
   match an independent Python calculation from the workbook. Show me the numbers.
3. Publish it as one self-contained page (Artifact) that anonymous viewers can open, and give me the link.

DASHBOARD CONTENT AND RULES  (full detail in "Prompt Dashboard/DASHBOARD_SPEC.md")
- Thai/English toggle, responsive for phone, iPad and large screens; executives aged 55–65 so large type and high contrast.
- Header line left→right: title · search box · orange hint on the right. Controls: Language, Year, Month, Week (Sunday–Saturday, database numbering),
  Based on (Np stocking | Selling), Main metric, Compare items, Voice, "N tanks · M invoices" (tank = บ่อ, invoice = ใบส่งของ).
- Overview tiles, trend, by hatchery / year, QC index table, Market area (Area | Region), Packing salinity, Top 20 customers, Tank table, glossary.
- %SR: numerator follows the Main metric (PL sold → "%SR Inv.", PL produced → "%SR PDT"); denominator is ALWAYS Np stocking bill, counted once per tank.
  Np stocking Actual appears only in Compare → Np basis. Tanks never sold are not in %SR: Damaged if stocked > 30 days before the last selling date, else In progress.
- QC index colours: green = better (higher %SR, TL, ADL; lower DOC, %CV, weight). No colour on Tanks, Np stocked, PL sold, %ST, Salinity.
- Tank table: show the first area/customer and a "+N" button; clicking it opens an extra row listing every invoice of that tank, clicking again closes it.
- Every chart, cell, row and bar is clickable to filter all charts; a second click removes the filter; chips show active filters with "Clear all".
- Customer names visible (executives need them). Tell me that anyone with the link can see them.

AFTER DELIVERY
Summarise in 5 lines: data counts, anything excluded or suspicious, the link, and what refreshes automatically (nothing, unless I ask for the nightly update).
```

## Nightly update (optional, add to the prompt)

```text
Every night at 23:59 (<TIMEZONE>) re-read the workbook from Google Drive (file id <ID>), run build_dashboard.py again, and republish the same
Artifact URL. If no row is newer than the last build, do nothing and report "0 new rows" in one line. Never delete or overwrite the source workbook.
```

## Change requests that were already made (keep them when regenerating)
Search box in the header row; Month and Week filters from the database; Compare items and Voice right after Main metric; Language before Year;
QC "scorecard" renamed **QC index**; Trend lines 70 % thicker, selected year thicker and darker; Full-screen button; customer feedback underline (green Success / grey Unsuccess) in the Tanks table; Np bill only as the default denominator; "+N" opens invoice rows; %SR column follows Main metric
("%SR Inv." / "%SR PDT").
