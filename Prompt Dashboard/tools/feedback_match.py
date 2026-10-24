"""Match customer feedback (Satisfied / Unsatisfied) to the invoices of the dashboard data object D.

Feedback workbooks need a header row containing: Hatchery, Packing Date, Customer Name, Feed Back, Section, Packing Tank
(and optionally "Sum of Total PL Selling (Mil.)"). Any sheet whose header row has these columns is read.

Key = hatchery + unit (Section) + tank + packing date = selling date.  The crop number is NOT used because some feedback files count
crops continuously (e.g. 8 for the 2026 Crop 1), while the QC file restarts the crop number every year.
Several customers may share a tank and date, so the customer name decides (exact spelling key, then >= 0.8 similarity, then the only
remaining candidate when its name is at least 0.5 similar, then packed quantity).
Result: column 'fb' on every invoice row: 1 = Success (Satisfied), 0 = Unsuccess (Unsatisfied), None = no feedback.
"""
import re, difflib, collections, warnings
import openpyxl
warnings.filterwarnings('ignore')

NEED = ['hatchery', 'packing date', 'customer name', 'feed back', 'section', 'packing tank']
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
                    if all(n in low for n in NEED): head = {n: low.index(n) for n in NEED}; head['qty'] = next((i for i, c in enumerate(low) if c.startswith('sum of total pl')), None)
                    continue
                d = r[head['packing date']]
                if not hasattr(d, 'strftime'): continue
                out.append(dict(h=_norm_h(r[head['hatchery']]), unit=str(r[head['section']]).strip(), tank=str(r[head['packing tank']]).strip(),
                                date=d.strftime('%Y-%m-%d'), cust=str(r[head['customer name']] or ''),
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
    used, fb, st = set(), {}, collections.Counter()
    st['feedback records'] = len(F)
    for f in F:
        c = [j for j in idx.get((hidx.get(f['h']), f['unit'], f['tank'], f['date']), []) if j not in used]
        if not c: st['no invoice for tank+date'] += 1; continue
        ck = [j for j in c if _name(cname(j)) == _name(f['cust'])]
        if ck:
            q = [j for j in ck if abs(pl(j) - f['qty']) <= max(3, f['qty'] * 1e-4)]; pick = (q or ck)[0]; st['same name'] += 1
        else:
            best = max(c, key=lambda j: _sim(f['cust'], cname(j)))
            s = _sim(f['cust'], cname(best))
            if s >= 0.8: pick = best; st['similar name'] += 1
            elif len(c) == 1 and s >= 0.5: pick = best; st['only candidate, name differs'] += 1
            else:
                q = [j for j in c if f['qty'] > 0 and abs(pl(j) - f['qty']) <= max(3, f['qty'] * 1e-4)]
                if len(q) == 1: pick = q[0]; st['by quantity'] += 1
                else: st['unmatched'] += 1; continue
        used.add(pick)
        if f['fb'] is not None: fb[pick] = f['fb']
        else: st['matched but blank feedback'] += 1
    D['rowCols'] = D['rowCols'] + ['fb']
    for j, r in enumerate(rows): r.append(fb.get(j))
    st['invoices with feedback'] = len(fb)
    return st
