"""
generate_dashboard.py — Fixed version
อ่านไฟล์ Excel Vijaya1 และ Vijaya2 แล้ว generate index.html อัตโนมัติ
"""
import pandas as pd
from openpyxl import load_workbook
import json, os, sys

FILES = {
    "Vijaya1": "Vijaya1_Daily_Record_V_2026.xlsx",
    "Vijaya2": "Vijaya2_Daily_Record_V_2026.xlsx",
}

def load_unit_data(filepath):
    if not os.path.exists(filepath):
        print(f"  [SKIP] ไม่พบไฟล์: {filepath}")
        return {}

    wb = load_workbook(filepath, read_only=True, data_only=True)

    # PL1 Raw Data — ใช้ index เพราะมีชื่อคอลัมน์ซ้ำกัน
    ws = wb['PL1 Raw Data']
    rows = list(ws.iter_rows(values_only=True))
    df_pl1 = pd.DataFrame(rows[1:], columns=range(len(rows[0])))
    df_pl1 = df_pl1.rename(columns={
        0: 'Tank_Crop', 4: 'Crop', 5: 'Unit', 6: 'Tank_No',
        12: 'Actual_density_L', 15: 'TL_PL1'
    })
    df_pl1 = df_pl1[df_pl1['Unit'].notna() & df_pl1['Tank_Crop'].notna()]

    # Raw Data
    ws2 = wb['Raw Data']
    rows2 = list(ws2.iter_rows(values_only=True))
    df_raw = pd.DataFrame(rows2[1:], columns=rows2[0])
    df_raw = df_raw[df_raw['Unit'].notna() & df_raw['Tank #Crop'].notna()]

    wb.close()

    def clean(lst):
        return [round(float(v), 3) if (v is not None and str(v) != 'nan') else None for v in lst]

    def build(dpu, dru, ptype):
        if ptype != 'ALL':
            dru = dru[dru['Type of Product'] == ptype]
            crops_in = set(dru['Crop'].dropna().unique())
            dpu = dpu[dpu['Crop'].isin(crops_in)]

        pl1g = dpu.groupby('Crop').agg(
            TL_PL1=('TL_PL1', 'mean'),
            density=('Actual_density_L', 'mean')
        ).reset_index()
        rawg = dru.groupby('Crop').agg(
            TL_1st=('TL-1st Pass QC', 'mean'),
            DOC_mean=('DOC-1st Pass QC', 'mean'),
            DOC_min=('DOC-1st Pass QC', 'min'),
            DOC_max=('DOC-1st Pass QC', 'max'),
        ).reset_index()

        merged = pl1g.merge(rawg, on='Crop', how='outer').sort_values('Crop')
        if merged.empty:
            return None
        return {
            'crops':    [int(c) for c in merged['Crop'].tolist()],
            'TL_PL1':  clean(merged['TL_PL1'].tolist()),
            'TL_1st':  clean(merged['TL_1st'].tolist()),
            'density': clean(merged['density'].tolist()),
            'DOC_mean':clean(merged['DOC_mean'].tolist()),
            'DOC_min': clean(merged['DOC_min'].tolist()),
            'DOC_max': clean(merged['DOC_max'].tolist()),
        }

    result = {}
    for unit in sorted(df_pl1['Unit'].dropna().unique()):
        dpu_u = df_pl1[df_pl1['Unit'] == unit]
        dru_u = df_raw[df_raw['Unit'] == unit]
        result[unit] = {p: build(dpu_u, dru_u, p) for p in ['ALL', 'PL4', 'PL12']}
    return result

print("กำลังอ่านข้อมูล Excel...")
ALL_DATA = {}
for h, fp in FILES.items():
    print(f"  {h}: {fp}")
    ALL_DATA[h] = load_unit_data(fp)

if not any(ALL_DATA.values()):
    print("ERROR: ไม่พบไฟล์ Excel")
    sys.exit(1)

DATA_JS = json.dumps(ALL_DATA, ensure_ascii=False)

HTML = '''<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Vijaya Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.2.0/chartjs-plugin-datalabels.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;background:#1e2a14;display:flex;align-items:flex-start;justify-content:flex-start;font-family:Tahoma,sans-serif;overflow:hidden}
.frame{width:360px;height:640px;background:#3a4a2e;position:absolute;top:0;left:0;display:flex;flex-direction:column;overflow:hidden;transform-origin:top left}
.frame::before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(0,0,0,0.07)1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,0.07)1px,transparent 1px);background-size:36px 36px;pointer-events:none;z-index:0}
.inner{position:relative;z-index:1;width:360px;height:640px;display:flex;flex-direction:column;padding:8px 8px 6px;gap:4px}
.hd{flex:0 0 50px;display:flex;align-items:center;justify-content:space-between;padding-bottom:5px;border-bottom:1px solid rgba(0,0,0,0.25)}
.hd-left{display:flex;flex-direction:column;gap:2px}
.badge{display:inline-flex;align-items:center;gap:4px;font-size:7px;letter-spacing:.1em;text-transform:uppercase;color:#a8e06e;background:rgba(168,224,110,0.15);border:1px solid rgba(168,224,110,0.28);border-radius:3px;padding:2px 6px}
.dot{width:5px;height:5px;border-radius:50%;background:#a8e06e;animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
.hd-title{font-size:14px;font-weight:800;color:#fff;letter-spacing:-.02em;line-height:1.1}
.hd-sub{font-size:7px;color:#e8ede0}
.hd-right{text-align:right}
.hd-n{font-size:25px;font-weight:800;color:#fff;line-height:1}
.hd-u{font-size:7px;color:#d0dcc0;letter-spacing:.06em}
.h-sel{flex:0 0 24px;display:flex;gap:5px;align-items:center}
.h-btn{flex:1;height:22px;border:none;border-radius:5px;cursor:pointer;font-family:Tahoma,sans-serif;font-size:9px;font-weight:700;transition:all .18s ease}
.h-btn.v1{background:rgba(168,224,110,0.18);color:#a8e06e;border:1px solid rgba(168,224,110,0.35)}
.h-btn.v1.active{background:#a8e06e;color:#1a2e10}
.h-btn.v2{background:rgba(255,224,133,0.18);color:#ffe085;border:1px solid rgba(255,224,133,0.35)}
.h-btn.v2.active{background:#ffe085;color:#2e200a}
.u-sel{flex:0 0 22px;display:flex;gap:4px;align-items:center;overflow-x:auto;scrollbar-width:none}
.u-sel::-webkit-scrollbar{display:none}
.u-btn{flex:0 0 auto;height:20px;min-width:34px;padding:0 7px;border:1px solid rgba(255,255,255,0.15);border-radius:4px;cursor:pointer;font-family:Tahoma,sans-serif;font-size:8.5px;font-weight:700;background:rgba(255,255,255,0.07);color:#b8c4a0;transition:all .15s ease;white-space:nowrap}
.u-btn.active{background:#fff;color:#1a2e10;border-color:#fff}
.pl-sel{flex:0 0 22px;display:flex;gap:5px;align-items:center}
.pl-btn{flex:1;height:20px;border:none;border-radius:4px;cursor:pointer;font-family:Tahoma,sans-serif;font-size:8px;font-weight:700;transition:all .15s ease;border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.07);color:#b8c4a0}
.pl-btn.active{color:#1a2e10;border-color:transparent}
.pl-btn.all.active{background:#d0dcc0}
.pl-btn.pl4.active{background:#ffe085;color:#2e200a}
.pl-btn.pl12.active{background:#7eb8f7;color:#0a1e3a}
.kpi-row{flex:0 0 40px;display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.kpi{background:#2e3c24;border:1px solid rgba(0,0,0,0.22);border-radius:5px;padding:4px 6px 3px;position:relative;overflow:hidden}
.kpi::after{content:"";position:absolute;top:0;left:0;right:0;height:2px}
.kpi.g::after{background:#a8e06e}.kpi.y::after{background:#ffe085}.kpi.o::after{background:#f4a44b}
.kpi-l{font-size:5.5px;letter-spacing:.07em;text-transform:uppercase;color:#e8ede0;margin-bottom:1px}
.kpi-v{font-size:14px;font-weight:800;line-height:1}
.kpi.g .kpi-v{color:#a8e06e}.kpi.y .kpi-v{color:#ffe085}.kpi.o .kpi-v{color:#f4a44b}
.kpi-u{font-size:5.5px;color:#c0d0a8}
.charts{flex:1;display:flex;flex-direction:column;gap:4px;min-height:0}
.panel{flex:1;background:#2e3c24;border:1px solid rgba(0,0,0,0.22);border-radius:6px;padding:5px 5px 4px;display:flex;flex-direction:column;min-height:0;overflow:hidden}
.p-head{flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;margin-bottom:2px}
.p-title{font-size:8px;font-weight:700;color:#fff}
.p-meta{font-size:6px;color:#c0d0a8}
.p-leg{flex:0 0 auto;display:flex;gap:7px;margin-bottom:3px;flex-wrap:wrap}
.li{display:flex;align-items:center;gap:3px;font-size:6.5px;color:#e8ede0}
.ls{width:7px;height:7px;border-radius:2px;display:inline-block}
.ll{width:12px;height:2px;border-radius:1px;display:inline-block}
.cw{flex:1;position:relative;min-height:0;background:#f8f7f2;border-radius:4px;border:1px solid rgba(0,0,0,0.09);overflow:hidden}
.cw canvas{position:absolute;inset:0;width:100%!important;height:100%!important}
.ft{flex:0 0 14px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid rgba(0,0,0,0.22);padding-top:3px}
.ft span{font-size:6px;color:#c0d0a8;letter-spacing:.05em}
</style>
</head>
<body>
<div class="frame" id="dash">
 <div class="inner">
  <div class="hd">
   <div class="hd-left">
    <span class="badge"><span class="dot"></span>HATCHERY DASHBOARD AUTO-UPDATE</span>
    <div class="hd-title" id="hd-title">VIJAYA 1 - UNIT A1</div>
    <div class="hd-sub">PL Performance - TL / Density / DOC</div>
   </div>
   <div class="hd-right">
    <div class="hd-n" id="hd-crops">-</div>
    <div class="hd-u">CROPS</div>
   </div>
  </div>
  <div class="h-sel">
   <button class="h-btn v1 active" onclick="selectHatchery('Vijaya1',this)">VIJAYA 1</button>
   <button class="h-btn v2" onclick="selectHatchery('Vijaya2',this)">VIJAYA 2</button>
  </div>
  <div class="u-sel" id="u-sel"></div>
  <div class="pl-sel">
   <button class="pl-btn all active" onclick="selectPL('ALL',this)">ALL</button>
   <button class="pl-btn pl4" onclick="selectPL('PL4',this)">PL4 <span style="font-size:6.5px;font-weight:400;opacity:.85">~DOC 9-10d</span></button>
   <button class="pl-btn pl12" onclick="selectPL('PL12',this)">PL12 <span style="font-size:6.5px;font-weight:400;opacity:.85">~DOC 12-16d</span></button>
  </div>
  <div class="kpi-row">
   <div class="kpi g"><div class="kpi-l">TL PL1 เฉลี่ย</div><div class="kpi-v" id="kv1">-</div><div class="kpi-u">mm</div></div>
   <div class="kpi y"><div class="kpi-l">TL 1st Pass</div><div class="kpi-v" id="kv2">-</div><div class="kpi-u">mm</div></div>
   <div class="kpi o"><div class="kpi-l">Density เฉลี่ย</div><div class="kpi-v" id="kv3">-</div><div class="kpi-u">ตัว/L</div></div>
  </div>
  <div class="charts">
   <div class="panel">
    <div class="p-head"><div class="p-title">TL (mm) - PL1 vs 1st Pass QC</div></div>
    <div class="p-leg">
     <div class="li"><span class="ls" style="background:#16642e"></span>TL PL1</div>
     <div class="li"><span class="ls" style="background:#0d2561"></span>TL 1st Pass</div>
     <div class="li"><span class="ll" style="background:#c0392b"></span><span style="color:#c0392b" id="std-label">STD >=7.5</span></div>
    </div>
    <div class="cw"><canvas id="cTL"></canvas></div>
   </div>
   <div class="panel">
    <div class="p-head">
     <div class="p-title">Actual Density (ตัว/L)</div>
     <div class="p-meta">แกนขวา = TL PL1</div>
    </div>
    <div class="p-leg">
     <div class="li"><span class="ls" style="background:#d2641e"></span>Density</div>
     <div class="li"><span class="ls" style="background:#1565c0"></span>TL PL1</div>
    </div>
    <div class="cw"><canvas id="cDn"></canvas></div>
   </div>
   <div class="panel">
    <div class="p-head">
     <div class="p-title">DOC ที่ 1st Pass (วัน)</div>
     <div class="p-meta">avg / min / max</div>
    </div>
    <div class="p-leg">
     <div class="li"><span class="ls" style="background:#4a2d8c"></span>เฉลี่ย</div>
     <div class="li"><span class="ll" style="background:#c0392b"></span>สูงสุด</div>
     <div class="li"><span class="ll" style="background:#0a5c4a"></span>ต่ำสุด</div>
    </div>
    <div class="cw"><canvas id="cDOC"></canvas></div>
   </div>
  </div>
  <div class="ft">
   <span id="ft-l">HATCHERY REPORT - AUTO GENERATED</span>
   <span id="ft-r">UNIT A1</span>
  </div>
 </div>
</div>
<script>
function scaleFrame(){var el=document.getElementById("dash");var s=Math.min(window.innerWidth/360,window.innerHeight/640);el.style.transform="scale("+s+")";el.style.left=((window.innerWidth-360*s)/2)+"px";el.style.top=((window.innerHeight-640*s)/2)+"px";}
scaleFrame();window.addEventListener("resize",scaleFrame);
var DATA=__DATA_JSON__;
var curH=Object.keys(DATA)[0],curU="",curPL="ALL";
var chartTL=null,chartDn=null,chartDOC=null;
var F="Tahoma,sans-serif",S=8,GC="rgba(13,37,97,0.09)";
var TT={backgroundColor:"#1c2b12",borderColor:"rgba(0,0,0,0.3)",borderWidth:1,titleColor:"#fff",bodyColor:"#b8c4a0",padding:5,titleFont:{size:7,family:F},bodyFont:{size:7,family:F}};
function axY(mn,mx,cb,lim){return{min:mn,max:mx,grid:{color:GC},border:{color:"transparent"},ticks:{color:"#0d2561",font:{size:S,family:F},maxTicksLimit:lim||4,callback:cb}};}
function axY2(mn,mx,cb){return{min:mn,max:mx,position:"right",grid:{display:false},border:{color:"transparent"},ticks:{color:"#1565c0",font:{size:S,family:F},maxTicksLimit:3,callback:cb}};}
var axX={grid:{display:false},border:{color:"transparent"},ticks:{color:"#0d2561",font:{size:S,family:F}}};
var bopt={responsive:false,maintainAspectRatio:false,animation:{duration:350},layout:{padding:{left:2,right:6,top:20,bottom:2}},plugins:{legend:{display:false},tooltip:TT}};
function avg(arr){var v=(arr||[]).filter(function(x){return x!=null;});return v.length?v.reduce(function(a,b){return a+b;},0)/v.length:null;}
function getData(){var h=DATA[curH]||{};var u=h[curU]||{};return u[curPL]||u["ALL"]||{crops:[],TL_PL1:[],TL_1st:[],density:[],DOC_mean:[],DOC_min:[],DOC_max:[]};}
function initCharts(){
  var d=getData();
  var labels=(d.crops||[]).map(function(c){return "C"+c;});
  var n=labels.length;
  var maxDens=n?Math.max.apply(null,(d.density||[]).filter(function(x){return x!=null;})):100;
  var stdVal=curPL==="PL4"?6.0:7.5;
  Chart.unregister(ChartDataLabels);
  if(chartTL){chartTL.destroy();chartTL=null;}
  if(chartDn){chartDn.destroy();chartDn=null;}
  if(chartDOC){chartDOC.destroy();chartDOC=null;}
  if(!n)return;
  chartTL=new Chart(document.getElementById("cTL"),{
    plugins:[ChartDataLabels],
    data:{labels:labels,datasets:[
      {type:"bar",data:d.TL_PL1,backgroundColor:"rgba(22,100,46,0.82)",borderColor:"#16642e",borderWidth:1.5,borderRadius:3,borderSkipped:false,yAxisID:"y",
        datalabels:{anchor:"end",align:"end",rotation:-90,color:"#16642e",font:{size:6,family:F,weight:"bold"},formatter:function(v){return v!=null?v.toFixed(2):""}}},
      {type:"bar",data:d.TL_1st,backgroundColor:"rgba(13,37,97,0.82)",borderColor:"#0d2561",borderWidth:1.5,borderRadius:3,borderSkipped:false,yAxisID:"y",
        datalabels:{anchor:"end",align:"end",rotation:-90,color:"#0d2561",font:{size:6,family:F,weight:"bold"},formatter:function(v,ctx){if(v==null)return"";var doc=d.DOC_mean[ctx.dataIndex];return v.toFixed(2)+(doc!=null?" D"+Math.round(doc):"");}}},
      {type:"line",data:Array(n).fill(stdVal),borderColor:"#c0392b",borderWidth:2,borderDash:[5,4],pointRadius:0,yAxisID:"y",datalabels:{display:false}}
    ]},
    options:Object.assign({},bopt,{scales:{y:axY(4.5,9.5,function(v){return v.toFixed(1);},5),x:axX}})
  });
  chartDn=new Chart(document.getElementById("cDn"),{
    plugins:[ChartDataLabels],
    data:{labels:labels,datasets:[
      {type:"bar",data:d.density,backgroundColor:"rgba(210,100,30,0.90)",borderColor:"#d2641e",borderWidth:1.5,borderRadius:3,yAxisID:"y",
        datalabels:{anchor:"end",align:"end",rotation:-90,color:"#d2641e",font:{size:6,family:F,weight:"bold"},formatter:function(v){return v!=null?v.toFixed(2):""}}},
      {type:"line",data:d.TL_PL1,borderColor:"#1565c0",borderWidth:2,pointRadius:3,pointBackgroundColor:"#1565c0",pointBorderColor:"#f8f7f2",pointBorderWidth:1.5,tension:0.4,yAxisID:"y2",backgroundColor:"transparent",
        datalabels:{anchor:"center",align:"bottom",rotation:-90,color:"#1565c0",font:{size:6,family:F,weight:"bold"},formatter:function(v){return v!=null?v.toFixed(2):""}}}
    ]},
    options:Object.assign({},bopt,{scales:{y:axY(0,Math.ceil(maxDens/50)*50+30,function(v){return Math.round(v);},4),y2:axY2(4.5,6.5,function(v){return v.toFixed(1);}),x:axX}})
  });
  chartDOC=new Chart(document.getElementById("cDOC"),{
    data:{labels:labels,datasets:[
      {type:"line",data:d.DOC_max,borderColor:"rgba(192,57,43,0.75)",borderWidth:1.5,borderDash:[4,3],pointRadius:0,fill:"+1",backgroundColor:"rgba(192,57,43,0.07)",tension:0.4},
      {type:"line",data:d.DOC_mean,borderColor:"#4a2d8c",borderWidth:2.5,pointRadius:3,pointBackgroundColor:"#4a2d8c",pointBorderColor:"#f8f7f2",pointBorderWidth:1.5,fill:false,tension:0.4},
      {type:"line",data:d.DOC_min,borderColor:"rgba(10,92,74,0.75)",borderWidth:1.5,borderDash:[4,3],pointRadius:0,fill:false,tension:0.4}
    ]},
    options:Object.assign({},bopt,{scales:{y:axY(6,18,function(v){return v+"d";},4),x:axX}})
  });
}
function updateUI(){
  var d=getData();
  var a1=avg(d.TL_PL1),a2=avg(d.TL_1st),a3=avg(d.density);
  document.getElementById("kv1").textContent=a1?a1.toFixed(2):"-";
  document.getElementById("kv2").textContent=a2?a2.toFixed(2):"-";
  document.getElementById("kv3").textContent=a3?Math.round(a3):"-";
  document.getElementById("hd-title").textContent=curH.toUpperCase()+" - UNIT "+curU;
  document.getElementById("hd-crops").textContent=(d.crops||[]).length||"-";
  document.getElementById("ft-l").textContent=curH.toUpperCase()+" - AUTO GENERATED";
  document.getElementById("ft-r").textContent="UNIT "+curU;
  var s=document.getElementById("std-label");
  if(s)s.textContent=curPL==="PL4"?"STD >=6.0":"STD >=7.5";
}
function renderUnits(){
  var units=Object.keys(DATA[curH]||{});
  var sel=document.getElementById("u-sel");
  sel.innerHTML="";
  if(!curU||!units.includes(curU))curU=units[0];
  units.forEach(function(u){
    var b=document.createElement("button");
    b.className="u-btn"+(u===curU?" active":"");
    b.textContent=u;
    b.onclick=function(){selectUnit(u,b);};
    sel.appendChild(b);
  });
}
function selectHatchery(h,btn){if(!DATA[h])return;curH=h;curU=Object.keys(DATA[h])[0];document.querySelectorAll(".h-btn").forEach(function(b){b.classList.remove("active");});btn.classList.add("active");renderUnits();updateUI();initCharts();}
function selectUnit(u,btn){curU=u;document.querySelectorAll(".u-btn").forEach(function(b){b.classList.remove("active");});btn.classList.add("active");updateUI();initCharts();}
function selectPL(p,btn){curPL=p;document.querySelectorAll(".pl-btn").forEach(function(b){b.classList.remove("active");});btn.classList.add("active");updateUI();initCharts();}
curU=Object.keys(DATA[curH]||{})[0]||"A1";
renderUnits();updateUI();initCharts();
</script>
</body>
</html>'''

HTML = HTML.replace('__DATA_JSON__', DATA_JS)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print("สร้าง index.html เสร็จแล้ว")
