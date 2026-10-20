# ฟอร์มข้อมูล / Data form

ทุกสาขากรอกข้อมูลลงไฟล์ Excel (.xlsx) หรือ Google Sheet เดียว **หนึ่งชีตต่อหนึ่งโรงเพาะ** (ชื่อชีตตั้งเองได้ แล้วระบุใน `config.json`)
แถวที่ 1 เป็นหัวตาราง ห้ามเปลี่ยนลำดับคอลัมน์ **1 แถว = 1 ใบส่งของ (การขายของบ่อหนึ่งให้ลูกค้าหนึ่งราย)**
ถ้าบ่อหนึ่งขายหลายครั้ง ให้ทำซ้ำข้อมูลบ่อ (คอลัมน์ A–Q) ในทุกแถวของบ่อนั้น Np แต่ละบ่อจะถูกนับครั้งเดียวโดยอัตโนมัติ
บ่อที่ลง Np แล้วยังไม่เคยขาย ให้ใส่แถวเดียวโดยเว้นคอลัมน์ R เป็นต้นไปว่าง (ระบบจัดเป็น "เสียหาย" ถ้าลงมานานเกิน 30 วันก่อนวันที่ขายล่าสุด)

Fill one workbook with **one sheet per hatchery**. Row 1 is the header; keep the column order. **One row = one invoice** (one tank sold to one customer);
repeat the tank columns (A–Q) on every row of the same tank. A stocked tank that was never sold gets one row with column R onwards empty.

| # | Col | Header | Type / unit | Used for |
|---|---|---|---|---|
| 1 | A | Hatchery | text | label only (use the sheet name in config) |
| 2 | B | Np stocking date | date | tank identity, month/week/year filters |
| 3 | C | Unit | text (A1, B1 …) | unit filter |
| 4 | D | Crop | integer | crop filter |
| 5 | E | Tank No. | text/number | tank identity (hatchery + unit + crop + tank + date) |
| 6 | F | Total volume (Ton.) | number | tank table |
| 7 | G | Np stocking Actual | million | only in Compare → Np basis |
| 8 | H | Np stocking bill | million | **denominator of every %SR** |
| 9 | I | Actual density | number | reference |
| 10 | J | Bill density | number | tank table |
| 11 | K | Brooder source | text | brooder filter |
| 12 | L | DoC | number | reference |
| 13 | M | %PL1 | number | reference |
| 14 | N | TL PL1 (mm) | mm | QC index |
| 15 | O | DOC 10 TL (mm) | mm | QC index |
| 16 | P | DOC 13 TL (mm) | mm | QC index |
| 17 | Q | %CV DOC13 | fraction (0.08 = 8 %) | QC index |
| 18 | R | Selling date | date | selling-date basis, month/week |
| 19 | S | Type of Product | text (PL4, PL12, Flight) | product filter |
| 20–22 | T–V | 1st pass QC (Doc, TL, %CV) | number | reference |
| 23 | W | DOC packing | days (0–50) | QC index (values outside 0–50 are treated as typos and ignored) |
| 24 | X | TL-Packing | mm | QC index |
| 25 | Y | %CV-Packing | fraction | QC index |
| 26 | Z | Weight (pcs/g)-packing | number | QC index |
| 27 | AA | %ST Packing | fraction (0.95 = 95 %) | QC index |
| 28 | AB | Customer Name | text | customer search, Top 20, tank table |
| 29 | AC | Market Area | text | Market area chart |
| 30 | AD | Market code | letters + optional digit (NOD1, SOD2, WB, CENTRAL) | region = the leading letters |
| 31 | AE | Packing Salinity | ppt (a cell like `10/12` is averaged) | salinity chart |
| 32 | AF | Total PL Selling (mil.) | million | **PL sold** and numerator of %SR |
| 33 | AG | Total Production (Mil.) | million | **PL produced** and numerator of %SR PDT |
| 34–35 | AH–AI | %SR Sell, %SR Production | fraction | reference only (the dashboard recomputes them) |
| 36 | AJ | ADL (mm) | mm/day | QC index |

Blank cells are allowed everywhere except B, C, D, E (tank identity). Dates must be real Excel dates.

## config.json

```json
{ "title": "Vijaya QC Dashboard",
  "hatcheries": [ {"sheet": "Vijaya1", "code": "VJ1"}, {"sheet": "Vijaya2", "code": "VJ2"} ],
  "source": "QC_Tank_Integrated_Report_2026.xlsx" }
```

## customer name map (optional)

`customer_name_map.json` = `{"VARIANT SPELLING (UPPER CASE)": "CANONICAL NAME", ...}`. The builder also merges spellings that differ only by
titles (MR, M/S, SRI), PVT LTD / PRIVATE LIMITED or punctuation. Add pairs the owner confirms are the same person.
