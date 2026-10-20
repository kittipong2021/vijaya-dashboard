# Dashboard specification (as built and approved)

Single HTML file, no external libraries, system fonts, light/dark theme, English/Thai toggle, responsive 9:16 (phone/tablet portrait) and 16:9.
Everything is client-side from one data object `D` (arrays of tanks `batches` and invoices `rows`).

## Layout (top to bottom)
1. **Header row, left → right (one line ≥ 900 px):** title "Summary of <hatcheries> Hatchery (first year to last year)" · search box · orange note on the right ("Click any bar, point, cell or row to filter every chart. Click again to remove.").
2. **Control row:** Language (ไทย/EN) · Year buttons · Month select · Week select · Based on (Np stocking | Selling) · Main metric · Compare items · Voice · counter "N tanks · M invoices" (tank = บ่อ, invoice = ใบส่งของ).
3. Active-filter chips with "Clear all".
4. **Overview tiles:** Tanks (sold / damaged / in progress), Np stocked, PL sold, %SR, DOC, TL, ADL, … each tile click = make it the main metric.
5. **Trend** (by month, calendar or running), **By hatchery**, **By year**.
6. **QC index** table (Group by year / month / hatchery / unit / crop / brooder / product / region): Tanks, Np stocked, PL sold, %SR Inv. (becomes %SR PDT when the main metric is PL produced), TL at PL1, TL at DOC10, TL at DOC13, TL at packing, ADL, DOC at packing, %CV at packing, Weight, %ST stress test, Salinity. Green shading = better: higher %SR, TL, ADL; lower DOC, %CV, weight. No colour on Tanks, Np stocked, PL sold, %ST, Salinity. Click a header to sort, a row to filter.
7. **Market area** (Area | Region) and **Packing salinity** bars; **Top 20 customers** horizontal bars (largest first) that follow every filter; unit/brooder/crop charts.
8. **Tank table** (25 per page, sortable). Columns: Np stocking date, Unit, Crop, Tank, Brooder, Np, PL, %SR, DOC, TL, ADL, ppt, Market area, Customer, Status. When a tank has several areas/customers the cell shows the first plus a **+N** button; click it to open an extra row under the tank listing every invoice (date, product, customer, area, region, PL); click again to close.
9. Glossary ("how numbers are calculated") and footer (source, build time, counts, tanks with %SR > 100).

## Calculations
* **Tank** = hatchery + unit + crop + tank no. + Np stocking date. **Invoice** = one selling row.
* **Np** of a tank = Np stocking **bill** (counted once per tank even if sold many times; tanks with bill 0/empty are left out of %SR). Np stocking *Actual* is used only when the user turns on Compare → Np basis (actual, else bill).
* **%SR (Inv.)** = Σ PL sold ÷ Σ Np bill over tanks that have sales × 100. **%SR PDT** = Σ PL produced ÷ Σ Np bill × 100. In the QC index and the overview the %SR column follows the Main metric (PL sold → %SR Inv., PL produced / %SR Production → %SR PDT); the denominator is always Np bill.
* **Damaged** = stocked, never sold, and stocked > 30 days before the latest selling date; otherwise **In progress**.
* **Week** = Sunday–Saturday, number = ISO week of the Monday − 1, week 0 merged into week 1 (matches the QC database weekly sheet). Month/week filters follow the *Based on* switch.
* Averages (DOC, TL, ADL, %CV, weight, %ST, salinity) are means over the invoices in the selection; PL1/DOC10/DOC13 lengths are means over tanks.
* DOC at packing outside 0–50 is ignored (typing error). Salinity cell with two values is averaged.
* Search box matches customer, tank, unit, crop, brooder, area, region, product, date and status words (e.g. `kolkata`, `vj2 c1 2026`, `damaged`, `2026-03`).
* Voice button reads the current summary aloud (browser speech synthesis).

## Data object `D`
`units, brooders, products, regions, areas, salBins, customers, hatch (codes), hlabel, title, built, source`,
`batchCols = [h,u,crop,tank,sd,vol,np,npa,dens,br,tl1,tl10,tl13,cv13,sr,flag]`, `rowCols = [b,ld,pr,ar,rg,sal,sb,pl,prod,doc,tl,cv,wt,st,adl,cu]`
(`b` = index into batches, `ar/rg/cu/pr/br/u` = index into the lookup lists, −1/null when empty).
