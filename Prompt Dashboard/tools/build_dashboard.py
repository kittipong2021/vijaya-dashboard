#!/usr/bin/env python3
"""Build the QC dashboard (one self-contained HTML file) from a QC Tank Integrated Report workbook.

usage: python3 build_dashboard.py config.json qc_report.xlsx out.html [customer_name_map.json]

config.json: {"title": "...", "hatcheries": [{"sheet": "Vijaya1", "code": "VJ1"}, ...], "source": "file label",
              "feedback": ["feedback_2025.xlsx", "feedback_2026.xlsx"]}   <- "feedback" is optional, see ../DATA_FORM.md
See ../DATA_FORM.md for the column layout every hatchery sheet must follow.
"""
import json, re, sys, datetime as dt, collections, os
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(sys.argv[1]))
xlsx, out = sys.argv[2], sys.argv[3]
namemap = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}

# column positions (0-based) in each hatchery sheet -- see DATA_FORM.md
C = dict(hatch=0, stock=1, unit=2, crop=3, tank=4, vol=5, npa=6, npb=7, dens=9, brooder=10,
         tl1=13, tl10=14, tl13=15, cv13=16, sell=17, prod=18, doc=22, tl=23, cv=24, wt=25, st=26,
         cust=27, area=28, mcode=29, sal=30, pl=31, production=32, sr=33, adl=35)
SAL_BINS = ['≤5', '6', '7', '8', '9–10', '11–12', '13–15', '>15']

def sal_bin(v):
    if v <= 5: return 0
    if v <= 8: return int(round(v)) - 5      # 6,7,8
    if v <= 10: return 4
    if v <= 12: return 5
    if v <= 15: return 6
    return 7

def num(x, nd=None):
    if x is None or x == '': return None
    try: f = float(x)
    except (TypeError, ValueError): return None
    return round(f, nd) if nd is not None else f

def doc_ok(v):
    """DOC at packing outside 0-50 days is a typing error (seen: 54, 93): leave it blank"""
    return v if v is not None and 0 <= v <= 50 else None

def salinity(x):
    """one number, or the average when the cell holds two values such as '10/12'"""
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    ps = [float(p) for p in re.findall(r'\d+(?:\.\d+)?', str(x))]
    return sum(ps) / len(ps) if ps else None

def _strip(u):
    return ' '.join(re.sub(r'^(M\s*/\s*S\.?|MS\.?|MR\.?|MRS\.?|SMT\.?|SRI)\s+', '', u).split())

def _key(s):
    """spelling-insensitive key: drops titles, PVT/LTD, punctuation"""
    s = s.upper().replace('&', ' AND ').replace('CENTRE', 'CENTER')
    s = re.sub(r'\bM\s*/\s*S\.?\b|\bMS\b|\bMR\.?\b|\bMRS\.?\b|\bSMT\.?\b|\bSRI\b|\bSHRI\b', '', s)
    s = re.sub(r'\bPVT\.?\s*LTD\.?\b|\bPRIVATE\s+LIMITED\b|\bPVT\b|\bLTD\b|\bLIMITED\b', '', s)
    return re.sub(r'[^A-Z0-9]', '', s)

def canon_customer(n):
    u = ' '.join(str(n).upper().split())
    return _strip(namemap.get(u, u))

def region_of(code):
    m = re.match(r'[A-Za-z]+', str(code or '').strip())
    return m.group(0).upper() if m else None

wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
units, brooders, products, regions, areas, customers = [], [], [], [], [], []
def idx(lst, v):
    if v not in lst: lst.append(v)
    return lst.index(v)

batches, bkey, rows = [], {}, []
for h, hc in enumerate(cfg['hatcheries']):
    for r in wb[hc['sheet']].iter_rows(min_row=2, values_only=True):
        if not r or r[C['stock']] is None or not isinstance(r[C['stock']], dt.datetime): continue
        unit = f"{hc['code']}·{r[C['unit']]}"
        key = (h, unit, r[C['crop']], str(r[C['tank']]), r[C['stock']].strftime('%Y-%m-%d'))
        if key not in bkey:
            br = r[C['brooder']]
            sr = num(r[C['sr']])
            bkey[key] = len(batches)
            batches.append([h, idx(units, unit), int(r[C['crop']]), str(r[C['tank']]), key[4],
                            num(r[C['vol']]), None, None, None, idx(brooders, str(br).strip()) if br else -1,
                            None, None, None, None, None, 0])
        b = batches[bkey[key]]
        # batch level values: take the first non-empty value found on any row of the tank
        for pos, col, nd, mul in [(6, 'npb', 4, 1), (7, 'npa', 4, 1), (8, 'dens', 1, 1), (10, 'tl1', 2, 1), (11, 'tl10', 2, 1),
                                  (12, 'tl13', 2, 1), (13, 'cv13', 2, 100), (14, 'sr', 1, 100)]:
            if b[pos] is None:
                v = num(r[C[col]])
                if v is not None: b[pos] = round(v * mul, nd)
        b[15] = 1 if (b[14] or 0) > 100 else 0
        sd = r[C['sell']]
        if isinstance(sd, dt.datetime):
            sal = salinity(r[C['sal']])
            area = str(r[C['area']] or '').strip().upper()
            rg = region_of(r[C['mcode']])
            rows.append([bkey[key], sd.strftime('%Y-%m-%d'), idx(products, str(r[C['prod']]).strip()),
                         idx(areas, area) if area else -1, idx(regions, rg) if rg else -1,
                         round(sal, 1) if sal is not None else None, sal_bin(sal) if sal is not None else -1,
                         num(r[C['pl']], 4), num(r[C['production']], 4), doc_ok(num(r[C['doc']])), num(r[C['tl']], 2),
                         round(num(r[C['cv']]) * 100, 2) if num(r[C['cv']]) is not None else None,
                         num(r[C['wt']]), round(num(r[C['st']]) * 100, 1) if num(r[C['st']]) is not None else None,
                         num(r[C['adl']], 3), idx(customers, canon_customer(r[C['cust']])) if r[C['cust']] else None])

# merge customer spellings that differ only in titles / PVT LTD / punctuation (most frequent spelling wins)
cnt = collections.Counter(r[15] for r in rows if r[15] is not None)
best = {}
for i, name in enumerate(customers):
    k = _key(name)
    if k not in best or cnt[i] > cnt[best[k]]: best[k] = i
newnames, remap = [], {}
for i, name in enumerate(customers):
    j = best[_key(name)]
    if j not in remap: remap[j] = len(newnames); newnames.append(customers[j])
    remap[i] = remap[j]
for r in rows:
    if r[15] is not None: r[15] = remap[r[15]]
customers = newnames
# brooder spellings differing only in case -> one entry
bcnt = collections.Counter(b[9] for b in batches)
bb, bmap, newbr = {}, {}, []
for i, name in enumerate(brooders):
    k = name.upper()
    if k not in bb or bcnt[i] > bcnt[bb[k]]: bb[k] = i
for i, name in enumerate(brooders):
    j = bb[name.upper()]
    if j not in bmap: bmap[j] = len(newbr); newbr.append(brooders[j])
    bmap[i] = bmap[j]
for b in batches:
    if b[9] >= 0: b[9] = bmap[b[9]]
brooders = newbr
D = dict(units=units, brooders=brooders, products=products, regions=regions, areas=areas, salBins=SAL_BINS,
         batchCols=['h', 'u', 'crop', 'tank', 'sd', 'vol', 'np', 'npa', 'dens', 'br', 'tl1', 'tl10', 'tl13', 'cv13', 'sr', 'flag'],
         rowCols=['b', 'ld', 'pr', 'ar', 'rg', 'sal', 'sb', 'pl', 'prod', 'doc', 'tl', 'cv', 'wt', 'st', 'adl', 'cu'],
         batches=batches, rows=rows, customers=customers,
         hatch=[h['code'] for h in cfg['hatcheries']], hlabel=[h['code']+' · '+h['sheet'] for h in cfg['hatcheries']], title=cfg.get('title', 'QC Dashboard'),
         built=dt.datetime.now().strftime('%Y-%m-%d %H:%M'), source=cfg.get('source', os.path.basename(xlsx)))
feedback_stats = None
if cfg.get('feedback'):     # optional: customer feedback files (Satisfied / Unsatisfied) -> underline on customer names
    sys.path.insert(0, HERE)
    import feedback_match
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    feedback_stats = feedback_match.attach(D, [os.path.join(base, p) for p in cfg['feedback']], [h['sheet'] for h in cfg['hatcheries']])
    print('feedback:', dict(feedback_stats))
tpl = open(os.path.join(HERE, 'dashboard_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(tpl.replace('/*DATA*/null', json.dumps(D, ensure_ascii=False, separators=(',', ':'))))
print(f'{len(batches)} tanks, {len(rows)} invoices, {len(customers)} customers -> {out}')
