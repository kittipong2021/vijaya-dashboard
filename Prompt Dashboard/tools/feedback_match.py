"""Match customer feedback (Satisfied / Unsatisfied) to the invoices of the dashboard data object D.

Feedback workbooks need a header row containing: Hatchery, Packing Date, Customer Name, Feed Back, Section, Packing Tank
(and optionally "Sum of Total PL Selling (Mil.)"). Any sheet whose header row has these columns is read.

Key = hatchery + unit (Section) + tank + packing date = selling date.  The crop number is NOT used because some feedback files count
crops continuously (e.g. 8 for the 2026 Crop 1), while the QC file restarts the crop number every year.
Several customers may share a tank and date, so the customer name decides (exact spelling key, then >= 0.8 similarity, then 0.5-0.8 similarity when it is the only candidate, or clearly better than the others, or has the same quantity;
a lower similarity is accepted only when the only candidate has exactly the same packed quantity; anything else is left unmatched rather than guessed).
Result: column 'fb' on every invoice row: 1 = Success (Satisfied), 0 = Unsuccess (Unsatisfied), None = no feedback.
"""
import re, difflib, collections, warnings
import openpyxl
warnings.filterwarnings('ignore')

NEED = ['hatchery', 'packing date', 'customer name', 'feed back', 'section', 'packing tank']
OPT = ['market code']
OK = {'SATISFIED': 1, 'NOT SATISFIED': 0, 'UNSATISFIED': 0}

def _name(s):
    s = str(s).upper().replace('&', ' AND ')
    s = re.sub(r'\bM\s*/\s*S\.?\b|\bMS\b|\bMR\.?\b|\bMRS\.?\b|\bSMT\.?\b|\bSRI\b|\bSHRI\b|\bPVT\.?\s*LTD\.?\b|\bPVT\b|\bLTD\b', '', s)
    return re.sub(r'[^A-Z0-9]', '', s)

def _sim(a, b): return difflib.SequenceMatcher(None, _name(a), _name(b)).ratio()
def _norm_h(s): return re.sub(r'\s+', '', str(s)).lower()

def read_feedback(paths):
    out = []
    for p in paths:
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        for ws in wb:
            rows = ws.iter_rows(values_only=True)
            head = None
            for r in rows:
                low = [str(c).strip().lower() if c is not None else '' for c in r]
                if head is None:
                    if all(n in low for n in NEED): head = {n: low.index(n) for n in NEED}; head['market code'] = low.index('market code') if 'market code' in low else None; head['qty'] = next((i for i, c in enumerate(low) if c.startswith('sum of total pl')), None)
                    continue
                d = r[head['packing date']]
                if not hasattr(d, 'strftime'): continue
                out.append(dict(h=_norm_h(r[head['hatchery']]), unit=str(r[head['section']]).strip(), tank=str(r[head['packing tank']]).strip(),
                                date=d.strftime('%Y-%m-%d'), cust=str(r[head['customer name']] or ''), mc=str(r[head['market code']]) if head.get('market code') is not None else '',
                                qty=float(r[head['qty']] or 0) if head['qty'] is not None else 0.0,
                                fb=OK.get(str(r[head['feed back']]).strip().upper())))
    return out

def attach(D, paths, hatch_sheets):
    """Adds column 'fb' to D['rows'] / D['rowCols'] and returns a stats Counter. hatch_sheets = sheet names in D['hatch'] order."""
    F = read_feedback(paths)
    hidx = {_norm_h(s): i for i, s in enumerate(hatch_sheets)}
    bl, rows, cust = D['batches'], D['rows'], D['customers']
    idx = collections.defaultdict(list)
    for j, r in enumerate(rows):
        b = bl[r[0]]
        idx[(b[0], D['units'][b[1]].split('·')[-1], str(b[3]), r[1])].append(j)
    ci = D['rowCols'].index('cu')
    cname = lambda j: cust[rows[j][ci]] if rows[j][ci] is not None else ''
    pl = lambda j: (rows[j][D['rowCols'].index('pl')] or 0) * 1e6
    used, fb, st, audit = set(), {}, collections.Counter(), []
    st['feedback records'] = len(F)
    for f in F:
        c = [j for j in idx.get((hidx.get(f['h']), f['unit'], f['tank'], f['date']), []) if j not in used]
        if not c: st['no invoice left for tank+date'] += 1; audit.append(dict(how='NO INVOICE LEFT', fb=f, inv=None, sim=0, cands=[])); continue
        ck = [j for j in c if _name(cname(j)) == _name(f['cust'])]
        ranked = sorted(c, key=lambda j: -_sim(f['cust'], cname(j)))
        s0 = _sim(f['cust'], cname(ranked[0])); s1 = _sim(f['cust'], cname(ranked[1])) if len(ranked) > 1 else 0
        if ck:
            q = [j for j in ck if abs(pl(j) - f['qty']) <= max(3, f['qty'] * 1e-4)]; pick = (q or ck)[0]; how = 'exact name'
        elif s0 >= 0.8: pick = ranked[0]; how = 'similar name (>= 0.8)'
        elif s0 >= 0.5 and (len(c) == 1 or s0 - s1 >= 0.15 or abs(pl(ranked[0]) - f['qty']) <= max(3, f['qty'] * 1e-4)):
            pick = ranked[0]; how = 'name 0.5-0.8 and clearly the best candidate (or same quantity)'
        elif len(c) == 1 and f['qty'] >= 10000 and abs(pl(c[0]) - f['qty']) <= max(3, f['qty'] * 1e-4):
            pick = c[0]; how = 'different name but the only candidate with exactly the same quantity'
        else:
            st['unmatched (names too different)'] += 1
            audit.append(dict(how='NOT MATCHED', fb=f, inv=None, sim=s0, cands=[(cname(j), round(pl(j))) for j in c])); continue
        st[how] += 1
        if how != 'exact name':
            audit.append(dict(how=how, fb=f, inv=pick, sim=_sim(f['cust'], cname(pick)), cands=[(cname(j), round(pl(j))) for j in c]))
        used.add(pick)
        if f['fb'] is not None: fb[pick] = f['fb']
        else: st['matched but blank feedback'] += 1
    D['rowCols'] = D['rowCols'] + ['fb']
    for j, r in enumerate(rows): r.append(fb.get(j))
    st['invoices with feedback'] = len(fb)
    D['_fbaudit'] = audit      # removed by the builder before the page is written
    return st
