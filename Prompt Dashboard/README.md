# Prompt Dashboard — QC Dashboard kit for hatchery branches

ชุดนี้ใช้สร้าง **QC Dashboard** (ไทย/อังกฤษ, ใช้ได้ทั้งมือถือ แท็บเล็ต และจอใหญ่) จากไฟล์ข้อมูล QC ของแต่ละสาขา
This kit builds the QC Dashboard (Thai / English, responsive) from a branch's QC workbook.

```
Prompt Dashboard/
├─ README.md                      this file
├─ PROMPT.md                      the full prompt (paste into Claude to recreate / change the dashboard)
├─ DATA_FORM.md                   the data form every branch fills in (36 columns + optional feedback files)
├─ DASHBOARD_SPEC.md              what the dashboard shows and how every number is calculated
├─ config.example.json            hatchery sheets + title
├─ customer_name_map.example.json spelling merges confirmed for Vijaya customers (start empty for a new branch)
└─ tools/
   ├─ dashboard_template.html     the dashboard code (HTML + CSS + JS, no libraries); data slot: /*DATA*/null
   ├─ build_dashboard.py          xlsx → dashboard HTML (one self-contained file)
   ├─ feedback_match.py           matches customer feedback (Satisfied/Unsatisfied) to invoices
   └─ make_form_template.py       blank data form with the right headers
```

## ใช้งาน 3 ขั้นตอน / Three steps
1. `python3 tools/make_form_template.py my_form.xlsx HatcheryA HatcheryB` → กรอกข้อมูลตาม `DATA_FORM.md` (หรือใช้ไฟล์ QC เดิมที่มีคอลัมน์ตรงกัน)
2. คัดลอก `config.example.json` เป็น `config.json` แล้วแก้ชื่อชีต/รหัสโรงเพาะ/ชื่อหัวเรื่อง
3. `pip install openpyxl` แล้วรัน
   `python3 tools/build_dashboard.py config.json my_form.xlsx dashboard.html [customer_name_map.json]`
   ได้ไฟล์ `dashboard.html` ไฟล์เดียว เปิดในเบราว์เซอร์ได้ทันที หรืออัปโหลดเป็น Claude Artifact / เว็บไซต์ภายในองค์กร

ปรับข้อมูลใหม่: แก้ไฟล์ xlsx แล้วรันขั้นตอนที่ 3 ซ้ำ (หน้าเป็น snapshot ไม่ดึงข้อมูลสดเอง)

## ผ่าน Claude / With Claude
เปิด Claude (Claude Code หรือแชต) แนบไฟล์ข้อมูล แล้ววางข้อความจาก `PROMPT.md` Claude จะสร้างและเผยแพร่ dashboard ให้
ถ้าต้องการให้ข้อมูลใหม่เข้าอัตโนมัติทุกคืน ให้ใช้หัวข้อ "Nightly update" ใน `PROMPT.md`

## ตรวจสอบแล้ว / Validated
ตัวสร้างนี้ให้ตัวเลขเดียวกับ dashboard ต้นแบบของ Vijaya (3,482 บ่อ, 4,244 ใบส่งของ, Np 4,038.87 ล้าน, PL sold 2,552.79 ล้าน, %SR 70.0)
