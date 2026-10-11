import json,base64,sys,io,openpyxl,datetime as dt,collections
MM={'NOD-1':'N-ODISHA-1','NOD-2':'N-ODISHA-2','SOD-1':'S-ODISHA-1','SOD-2':'S-ODISHA-2','WB-2':'WB','WB-3':'WB','WB-4':'WB','Gujarat-N':'GJ'}
def mc(c):
    c=str(c).strip() if c else ''
    if c in MM: return MM[c]
    if c.startswith('CENTRAL-'): return 'C'+c.split('-')[1]
    return c
def agg(xlsx_bytes, after):
    wb=openpyxl.load_workbook(io.BytesIO(xlsx_bytes),data_only=True)
    g=collections.OrderedDict(); rows=[]
    for n in ['Vijaya1','Vijaya2']:
        for r in wb[n].iter_rows(min_row=2,values_only=True):
            if isinstance(r[17],dt.datetime) and r[27]: rows.append(r)
    rows.sort(key=lambda r:(r[17],r[0],str(r[27])))
    for r in rows:
        if r[17]<=after: continue
        k=(r[0].replace('Vijaya','Vijaya '),r[17].strftime('%Y-%m-%d'),r[18],' '.join(str(r[27]).upper().split()))
        d=g.setdefault(k,{'qty':0,'name':' '.join(str(r[27]).split()),'mc':set()})
        d['qty']+=(r[31] or 0)*1e6; d['mc'].add(mc(r[29]))
    return g,max(r[17] for r in rows)
if __name__=='__main__':
    d=json.load(open(sys.argv[1])); b=base64.b64decode(d['content'])
    open('qc_latest.xlsx','wb').write(b)
    after=dt.datetime.strptime(sys.argv[2],'%Y-%m-%d')
    g,mx=agg(b,after)
    print('max date in QC',mx,'new groups',len(g))
    for k,v in g.items(): print(k,round(v['qty']),sorted(v['mc']))
