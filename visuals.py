"""Create local interactive visual evidence for the SpaceX capstone report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / ".pydeps"))

import folium
import pandas as pd
import plotly


def create_map():
    data = pd.read_csv(ROOT / "dataset_part_2.csv")
    site_data = (
        data.groupby(["LaunchSite", "Latitude", "Longitude"], as_index=False)["Class"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )
    view = folium.Map(location=[34.5, -96], zoom_start=4, tiles="OpenStreetMap", control_scale=True)
    for row in site_data.itertuples():
        name = row.LaunchSite
        folium.CircleMarker(
            location=[row.Latitude, row.Longitude],
            radius=12 + 0.13 * row.count,
            color="#1a5f7a",
            fill=True,
            fill_color="#3f91b2",
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{name}</b><br>{row.count} launches<br>"
                f"{row.sum} successful landings<br>{row.mean:.1%} landing rate",
                max_width=260,
            ),
            tooltip=f"{name}: {row.mean:.1%} ({row.sum}/{row.count})",
        ).add_to(view)
    legend = '<div style="position:fixed;bottom:30px;left:30px;z-index:9999;' \
        'background:white;border:1px solid #8aa7b7;padding:12px 16px;' \
        'font:14px Arial;box-shadow:0 2px 8px #0002"><b>Launch sites</b><br>'
    legend += '<br>'.join(
        f'{row.LaunchSite}: {row.sum}/{row.count} ({row.mean:.1%})'
        for row in site_data.itertuples()
    )
    view.get_root().html.add_child(folium.Element(legend + '</div>'))
    view.save(str(ROOT / "launch_sites_map.html"))


def create_dashboard():
    data = pd.read_csv(ROOT / "spacex_launch_dash.csv")
    records = data[["Flight Number", "Launch Site", "class", "Payload Mass (kg)"]].to_dict("records")
    plotly_js = (Path(plotly.__file__).parent / "package_data" / "plotly.min.js").read_text(encoding="utf-8")
    page = """<!doctype html>
<html lang="en"><meta charset="utf-8">
<title>SpaceX Falcon 9 Launch Outcomes</title>
<style>
body {font: 16px Arial,sans-serif; margin:0; color:#203545; background:#f6f9fb}
header {background:#173c56;color:white;padding:25px 4%}
h1 {margin:0;font-size:31px} header p {margin:8px 0 0;color:#cfe5ef}
main {padding:26px 4%} .controls {display:flex;gap:28px;align-items:center;flex-wrap:wrap}
select,input {font:inherit;padding:7px} #site {min-width:230px}
.charts {display:grid;grid-template-columns: 1fr 1.3fr;gap:20px;margin-top:18px}
.chart {background:white;border:1px solid #d7e1e7;border-radius:7px;min-height:425px}
.note {font-size:13px;color:#5b6b76}
@media(max-width:900px){.charts{grid-template-columns:1fr}}
</style>
<header><h1>SpaceX Falcon 9 Launch Outcomes</h1>
<p>Interactive view of the IBM Skills Network dashboard dataset (56 launches)</p></header>
<main><div class="controls">
<label>Launch site <select id="site"></select></label>
<label>Payload range: <span id="rangeLabel"></span><br>
<input id="minPayload" type="range" min="0" max="10000" step="250" value="0">
<input id="maxPayload" type="range" min="0" max="10000" step="250" value="10000"></label>
</div>
<div class="charts"><div id="pie" class="chart"></div><div id="scatter" class="chart"></div></div>
<p class="note">Source: IBM Skills Network spacex_launch_dash.csv. Success refers to first-stage landing; this is a historical teaching dataset.</p>
</main><script>__PLOTLY_JS__</script><script>
const rows=__DATA__;
const sites=['All sites',...new Set(rows.map(r=>r['Launch Site']))];
const siteSelect=document.getElementById('site');
sites.forEach(s=>{const o=document.createElement('option');o.textContent=s;siteSelect.appendChild(o)});
function refresh(){
 const site=siteSelect.value, min=+document.getElementById('minPayload').value,max=+document.getElementById('maxPayload').value;
 const low=Math.min(min,max),high=Math.max(min,max);
 document.getElementById('rangeLabel').textContent=low.toLocaleString()+'–'+high.toLocaleString()+' kg';
 const subset=rows.filter(r=>(site==='All sites'||r['Launch Site']===site)&&r['Payload Mass (kg)']>=low&&r['Payload Mass (kg)']<=high);
 let labels=[],values=[],title='';
 if(site==='All sites'){
   labels=sites.slice(1);
   values=labels.map(s=>subset.filter(r=>r['Launch Site']===s&&r.class===1).length);
   title='Successful landings by launch site';
 } else {
   labels=['Successful landing','Other outcome'];
   values=[subset.filter(r=>r.class===1).length,subset.filter(r=>r.class===0).length];
   title='Outcomes at '+site;
 }
 Plotly.react('pie',[{type:'pie',labels,values,hole:0.25,marker:{colors:['#2d8eaa','#e18d64','#6993b2','#8d75a7']},textinfo:'label+value'}],
   {title,margin:{t:70,b:30,l:20,r:20},paper_bgcolor:'white'});
 const launchSuccess=subset.filter(r=>r.class===1),launchFailure=subset.filter(r=>r.class===0);
 Plotly.react('scatter',[
  {type:'scatter',mode:'markers',name:'Successful landing',x:launchSuccess.map(r=>r['Payload Mass (kg)']),y:launchSuccess.map(r=>r['Flight Number']),marker:{color:'#2d8eaa',size:10}},
  {type:'scatter',mode:'markers',name:'Other outcome',x:launchFailure.map(r=>r['Payload Mass (kg)']),y:launchFailure.map(r=>r['Flight Number']),marker:{color:'#e18d64',size:10}}],
  {title:'Payload mass and launch outcome',xaxis:{title:'Payload mass (kg)'},yaxis:{title:'Flight number'},margin:{t:70,b:70,l:65,r:20},paper_bgcolor:'white'});
}
['site','minPayload','maxPayload'].forEach(id=>document.getElementById(id).addEventListener('input',refresh));
refresh();
</script></html>"""
    page = page.replace("__PLOTLY_JS__", plotly_js).replace("__DATA__", json.dumps(records))
    (ROOT / "launch_dashboard.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    create_map()
    create_dashboard()
    print("Created launch_sites_map.html and launch_dashboard.html")
