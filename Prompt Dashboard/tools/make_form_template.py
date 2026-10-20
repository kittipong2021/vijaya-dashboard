#!/usr/bin/env python3
"""Create the blank data form (xlsx) a branch fills in: python3 make_form_template.py out.xlsx VJ1 VJ2 ..."""
import sys, datetime as dt, openpyxl
HEAD = ['Hatchery', 'Np stocking date', 'Unit', 'Crop', 'Tank No.', 'Total volume (Ton.)', 'Np stocking Actual', 'Np stocking bill',
        'Actual density', 'Bill density', 'Brooder source', 'DoC', '%PL1', 'TL PL1 (mm)', 'DOC 10 TL (mm)', 'DOC 13 TL (mm)', '%CV DOC13',
        'Selling date', 'Type of Product', 'Doc-1st pass QC', 'TL-1st pass QC', '%CV-1st pass QC', 'DOC packing', 'TL-Packing',
        '%CV-Packing', 'Weight (pcs/g)-packing', '%ST Packing', 'Customer Name', 'Market Area', 'Market code', 'Packing Salinity',
        'Total PL Selling (mil.)', 'Total Production (Mil.)', '%SR Sell', '%SR Production', 'ADL (mm)']
EX = ['SAMPLE1', dt.datetime(2026, 1, 3), 'C1', 1, 1, 9, 2.4, 2.4, 266.7, 266.7, 'SIS', 7, 1, 5.5, 6.7, 8.2, 0.08, dt.datetime(2026, 1, 17),
      'PL12', 17, 9.9, 0.07, 17, 9.96, 0.07, 300, 0.95, 'EXAMPLE CUSTOMER', 'KAKINADA', 'CENTRAL', 8, 1.83, 2.1, 0.76, 0.88, 0.414]
wb = openpyxl.Workbook(); wb.remove(wb.active)
for name in sys.argv[2:] or ['Hatchery1']:
    ws = wb.create_sheet(name); ws.append(HEAD); ws.append(EX); ws.freeze_panes = 'A2'
    for c, w in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', [12, 16, 8, 6, 8, 12, 12, 12]): ws.column_dimensions[c].width = w
wb.save(sys.argv[1]); print('wrote', sys.argv[1])
