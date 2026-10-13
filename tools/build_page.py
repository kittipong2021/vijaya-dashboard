"""Build the public sales page from the Google Sheet values.

usage: python3 tools/build_page.py sheet_values.json out.html
sheet_values.json: output of Sheets get_values for '2023-2026'!A2:J (key "values").
"""
import json, re, sys, os

def grp(m):
    if m.startswith('N-ODISHA'): return 0
    if m.startswith('S-ODISHA'): return 1
    if m == 'WB': return 2
    if re.match(r'^C\d+$', m): return 3
    return 4

def main(src, dst):
    values = json.load(open(src))['values']
    H = {'Vijaya 1': 0, 'Vijaya 2': 1}
    P = {'PL12': 0, 'PL4': 1}
    names, seen, rows = [], {}, []
    for r in values:
        r = list(r) + [''] * (10 - len(r))
        q = str(r[9]).replace(',', '')
        if not q or r[0] not in H or r[2] not in P:
            continue
        ds = str(r[1])
        if '-' in ds:
            yy, mm, dd = map(int, ds.split('-'))
        else:
            dd, mm, yy = map(int, ds.split('/'))
        c = seen.setdefault(r[5], len(seen))
        if c == len(names):
            names.append(r[5])
        rows.append([f'{yy:04d}-{mm:02d}-{dd:02d}', H[r[0]], P[r[2]], c, grp(r[6]), round(float(q))])
    rows.sort(key=lambda x: x[0])
    tpl = open(os.path.join(os.path.dirname(__file__), 'page_template.html')).read()
    tpl = tpl.replace('/*NAMES*/[]', json.dumps(names, ensure_ascii=False, separators=(',', ':')))
    tpl = tpl.replace('/*DATA*/[]', json.dumps(rows, separators=(',', ':')))
    open(dst, 'w').write(tpl)
    print('rows', len(rows), 'customers', len(names), 'last', rows[-1][0])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
