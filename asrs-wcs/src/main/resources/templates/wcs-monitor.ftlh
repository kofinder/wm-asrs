<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASRS · WCS Communication Monitor</title>
<style>
:root{--bg:#f1f4f8;--card:#fff;--ink:#162a40;--muted:#60738a;--line:#dfe7ef;--navy:#11293f;--blue:#2264b7;--green:#168052;--amber:#9b651c;--red:#af3942;--teal:#187a8b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}button,select{font:inherit}
a{color:var(--blue)}.head{background:var(--navy);color:white;padding:25px max(calc((100vw - 1320px)/2),28px);display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.brand{font-size:24px;line-height:1.2;font-weight:750;letter-spacing:-.4px}.subhead{font-size:12px;color:#b5c8da;margin-top:6px}.head a{color:#e5f2ff;text-decoration:none;border:1px solid #4b6881;border-radius:8px;padding:9px 13px}.container{max-width:1320px;margin:0 auto;padding:25px 22px 50px}
.lead{color:var(--muted);margin:0 0 18px}.toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px}.pill{padding:6px 10px;border-radius:999px;background:#e6eef8;color:#355a84;font-weight:700;font-size:12px}.pill.good{background:#ddf5e9;color:var(--green)}.pill.bad{background:#ffeded;color:var(--red)}.small{font-size:12px;color:var(--muted)}.toolbar button{background:#fff;border:1px solid var(--line);border-radius:7px;padding:7px 11px;cursor:pointer}.toolbar button:hover{border-color:#85abd8}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:12px 0 19px}.kpi,.panel{background:var(--card);border:1px solid var(--line);border-radius:13px;box-shadow:0 4px 15px rgba(16,44,75,.035)}.kpi{padding:17px 18px}.kpi small{color:var(--muted);font-weight:600;display:block;margin-bottom:7px}.kpi strong{font-size:26px;line-height:1;letter-spacing:-.7px}.kpi .under{font-size:11px;color:var(--muted);margin-top:7px}.panel{padding:18px;margin-bottom:17px}.sectionline{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}.sectionline h2{margin:0 0 4px;font-size:17px;letter-spacing:-.2px}.sectionline p{margin:0;font-size:12px;color:var(--muted)}
.flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-top:19px}.step{border-radius:11px;border:1px solid var(--line);padding:14px;background:#fbfdff;min-height:116px;position:relative}.step::after{content:'→';position:absolute;right:-14px;top:37px;color:#6c8aad;font-size:21px;z-index:2}.step:last-child::after{content:none}.step small{color:var(--muted);display:block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.4px}.step strong{display:block;margin:4px 0;font-size:16px}.step p{margin:5px 0 0;color:var(--muted);font-size:11px}.http{border-top:3px solid var(--blue)}.planner{border-top:3px solid #8660c7}.ua{border-top:3px solid #df9445}.feedback{border-top:3px solid var(--green)}
.grid2{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(320px,1fr);gap:17px}.grid2>.panel{min-width:0}
table{width:100%;border-collapse:collapse;font-size:12px;text-align:left}th{color:#556b7f;font-size:11px;background:#f4f7fa;text-transform:uppercase;letter-spacing:.2px}td,th{padding:11px 10px;border-bottom:1px solid #e7edf2;vertical-align:top}tbody tr:last-child td{border-bottom:0}tr.clickable{cursor:pointer}tr.clickable:hover{background:#f3f8ff}tr.selected{background:#e9f3ff}.tablewrap{overflow:auto;margin-top:15px;border:1px solid var(--line);border-radius:9px;max-height:440px}.mono{font:11px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;word-break:break-word}.tag{font-size:10px;font-weight:750;letter-spacing:.1px;padding:4px 7px;border-radius:5px;white-space:nowrap;background:#e8eef6;color:#355c81}.tag.good{background:#e0f5e9;color:#146c47}.tag.warn{background:#fff1d8;color:#9a671d}.tag.err{background:#ffe6e6;color:#a53a45}.muted{color:var(--muted)}.detail{background:#15283b;border:1px solid #26425d;border-radius:9px;padding:15px;margin-top:13px;overflow:auto;color:#e7f5ff;min-height:220px;max-height:450px;white-space:pre-wrap;word-break:break-word;font:12px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace}.fieldgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.field{background:#f5f8fb;border-radius:7px;padding:8px 11px}.field small{font-size:11px;color:var(--muted)}.field div{font-weight:650;word-break:break-word}.filters{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:15px}.filters select{min-width:120px;max-width:100%;padding:8px 10px;background:white;border:1px solid #cbd9e6;border-radius:8px;color:var(--ink)}.filters label{font-size:12px;font-weight:650}.empty{padding:24px;color:var(--muted);text-align:center}.warning{padding:11px 14px;background:#fff8e7;border:1px solid #f3e2b7;border-radius:8px;font-size:12px;color:#805a16;margin-top:12px}.footer{font-size:12px;color:var(--muted);margin-top:18px}.listflex{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}.listflex span{display:inline-flex;align-items:center;background:#f2f7fc;padding:6px 9px;border-radius:6px;color:#3a5f83;font-size:11px}.errorbox{background:#fff0f0;border:1px solid #eccaca;color:#a43f4a;border-radius:8px;padding:10px 13px;margin-bottom:14px;display:none}
@media(max-width:950px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.grid2{grid-template-columns:1fr}.flow{grid-template-columns:repeat(2,minmax(0,1fr))}.step:nth-child(2)::after{content:none}}
@media(max-width:560px){.head{padding:22px 16px}.container{padding:16px 12px}.brand{font-size:20px}.kpis{gap:9px}.flow{grid-template-columns:1fr}.step::after{content:none}.fieldgrid{grid-template-columns:1fr}.panel{padding:14px}}
</style>
</head>
<body>
<header class="head"><div><div class="brand">WCS · Communication Monitor</div><div class="subhead">ASRS lab · Kotlin / Spring Boot / FreeMarker · Messages observed from the running application</div></div><a href="http://localhost:8081/" target="_blank" rel="noopener noreferrer">Open WMS dashboard</a></header>
<main class="container">
<p class="lead">Understand what WCS receives from WMS, sends to ROS 2 and the PLC, and reads back as acknowledgment and completion. Select a task or event to inspect actual application-level values.</p>
<div class="toolbar"><span id="connection" class="pill">Connecting…</span><span class="small" id="updated">No live data yet</span><button type="button" id="refresh">Refresh now</button><span class="small">Auto-refresh every 2 seconds</span></div>
<div id="error" class="errorbox" role="alert"></div>
<section class="kpis">
<div class="kpi"><small>WCS tasks</small><strong id="total">—</strong><div class="under">In-memory task ledger</div></div>
<div class="kpi"><small>Completed</small><strong id="complete">—</strong><div class="under">PLC verification passed</div></div>
<div class="kpi"><small>Latest PLC command ID</small><strong id="cmd">—</strong><div class="under">From OPC UA status</div></div>
<div class="kpi"><small>PLC machine state</small><strong id="machine">—</strong><div class="under" id="ready">Waiting for status</div></div>
</section>
<section class="panel">
<div class="sectionline"><div><h2>Communication architecture</h2><p>Protocol and message type at each boundary</p></div><span class="pill">Read-only · Simulation</span></div>
<div class="flow">
<div class="step http"><small>01 · HTTP REST</small><strong>WMS → WCS</strong><p><code>POST /api/tasks/putaway</code> or <code>/retrieval</code><br>JSON pallet, rack and task ID</p></div>
<div class="step planner"><small>02 · HTTP REST</small><strong>WCS ↔ ROS 2</strong><p><code>POST /plan</code><br>JSON rack target → coordinates and approval</p></div>
<div class="step ua"><small>03 · OPC UA</small><strong>WCS → PLC</strong><p>Write <code>TargetLocation</code>, <code>CommandOperation</code>, then <code>CommandId</code></p></div>
<div class="step feedback"><small>04 · OPC UA / REST</small><strong>PLC → WCS → WMS</strong><p>Read acknowledgment and completion IDs; WMS polls WCS task status</p></div>
</div>
<div class="warning">OPC UA writes are <strong>three separate lab writes</strong>, not an atomic PLC transaction. “GOOD” means the OPC UA write succeeded, <strong>not</strong> that the crane completed a movement. Only matching feedback confirms completion.</div>
</section>
<div class="grid2">
<section class="panel">
<div class="sectionline"><div><h2>WCS task ledger</h2><p>Select a row to filter the communication events for that WMS task</p></div><span class="small" id="taskCount">0 tasks</span></div>
<div class="tablewrap"><table><thead><tr><th>Pallet / operation</th><th>Rack</th><th>WCS task / PLC cmd</th><th>Status</th></tr></thead><tbody id="taskRows"><tr><td colspan="4" class="empty">Waiting for tasks…</td></tr></tbody></table></div>
</section>
<section class="panel">
<div class="sectionline"><div><h2>Live PLC feedback</h2><p>Values read directly from WCS's OPC UA client</p></div><span class="pill" id="plcConnection">Checking…</span></div>
<div id="plcFields" class="fieldgrid"><div class="empty">Loading…</div></div>
</section>
</div>
<div class="grid2">
<section class="panel">
<div class="sectionline"><div><h2>Communication event log</h2><p>Click an event to inspect its values on the right</p></div><span class="small" id="eventCount">0 events</span></div>
<div class="filters"><label for="correlation">Task</label><select id="correlation"><option value="ALL">All traces</option></select><label for="protocol">Channel</label><select id="protocol"><option value="ALL">All channels</option><option value="REST">HTTP / JSON</option><option value="OPC UA">OPC UA</option><option value="INTERNAL">WCS internal</option></select><button type="button" id="clearSelection" style="padding:8px 10px;border-radius:8px;border:1px solid #d0dae6;background:white;cursor:pointer">Show all</button></div>
<div class="tablewrap"><table><thead><tr><th>Time</th><th>From → To</th><th>Message</th><th>Result</th></tr></thead><tbody id="eventRows"><tr><td colspan="4" class="empty">No events yet. Submit a task from WMS.</td></tr></tbody></table></div>
</section>
<section class="panel">
<div class="sectionline"><div><h2>Selected message</h2><p>Actual logical payload recorded at the application boundary</p></div><button id="copy" type="button" style="background:#fff;border:1px solid #d0dae6;border-radius:8px;padding:7px 11px;cursor:pointer">Copy JSON</button></div>
<div id="messageMeta" class="listflex"><span>Select an event</span></div>
<pre id="messageJson" class="detail">Select a message in the event log to inspect its fields.</pre>
<div class="small">This view is not a packet capture. Subscription updates use the global <code>PLC-LIVE</code> trace; task-specific acknowledgment and verification use the WMS task ID.</div>
</section>
</div>
<p class="footer">Educational simulation only. The last 350 communication events are held in WCS memory and reset when WCS restarts. No database, authentication, packet-level audit, or certified safety logging is provided. Never use this monitor to send real machinery commands.</p>
</main>
<script>
(function(){
'use strict';
const el = id => document.getElementById(id);
let last = null, selected = null, refreshing = false;
const emptyRow = (colspan, text) => { const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=colspan;td.className='empty';td.textContent=text;tr.appendChild(td);return tr;};
const td = (text, cl) => { const node=document.createElement('td');node.textContent=String(text == null ? '—' : text);if(cl)node.className=cl;return node;};
const shortId = text => {const s=String(text||'');return s.length>22?s.slice(0,11)+'…'+s.slice(-6):s;};
const fmtTime = iso => {try{return new Date(iso).toLocaleTimeString();}catch(_){return iso;}};
function setText(id, text){el(id).textContent=String(text == null ? '—':text);}
function badge(outcome){const b=document.createElement('span');const x=String(outcome||'');b.className='tag'+(/ERROR|REJECTED|BAD/.test(x)?' err':/UNCERTAIN|RUNNING/.test(x)?' warn':/GOOD|COMPLETED|ACKNOWLEDGED|APPROVED|VERIFIED|CONNECTED|ACCEPTED/.test(x)?' good':'');b.textContent=x;return b;}
function renderTasks(data){const rows=el('taskRows');rows.replaceChildren();const tasks=data.tasks||[];setText('taskCount',tasks.length+' tasks');tasks.slice(0,35).forEach(t=>{const row=document.createElement('tr');row.className='clickable';const correlation=t.externalTaskId||'DIRECT';row.onclick=()=>{el('correlation').value=correlation;selected=null;renderEvents(last);};const p=td(t.palletId+' / '+(t.operation||'PUTAWAY'));const sub=document.createElement('div');sub.className='mono muted';sub.textContent=shortId(t.externalTaskId||t.taskId);p.append(sub);row.append(p,td(t.targetLocation),td(shortId(t.taskId)+'\n#'+t.commandId,'mono'));const status=document.createElement('td');status.append(badge(t.status));row.append(status);rows.append(row);});if(!tasks.length)rows.append(emptyRow(4,'No tasks yet. Submit a putaway in WMS.'));}
function renderPlc(data){const st=data.plcStatus||{};const panel=el('plcFields');panel.replaceChildren();const badgeEl=el('plcConnection');badgeEl.textContent=data.plcOnline?'CONNECTED':'UNAVAILABLE';badgeEl.className='pill '+(data.plcOnline?'good':'bad');const fields=['Ready','Busy','MachineState','Position','CommandOperation','CommandId','AcceptedCommandId','CompletedCommandId','RejectedCommandId','PickupCommandId','ReleasedCommandId','FaultCode','AxisXPositionMm','AxisZPositionMm'];fields.forEach(key=>{const node=document.createElement('div');node.className='field';const title=document.createElement('small');title.textContent=key;const value=document.createElement('div');value.textContent=Object.prototype.hasOwnProperty.call(st,key)?String(st[key]):'—';node.append(title,value);panel.append(node);});setText('cmd',st.CommandId);setText('machine',st.MachineState);setText('ready',data.plcOnline?('Ready: '+st.Ready+' · Busy: '+st.Busy):'OPC UA read unavailable');}
function updateCorrelations(events){const select=el('correlation');const old=select.value;const found=new Map();events.forEach(e=>{if(!found.has(e.correlationId))found.set(e.correlationId,e);});select.replaceChildren(new Option('All traces','ALL'));for(const [id] of found){select.add(new Option(shortId(id),id));}select.value=[...found.keys()].includes(old)?old:'ALL';}
function renderEvents(data){if(!data)return;const rows=el('eventRows');rows.replaceChildren();const group=el('correlation').value;const proto=el('protocol').value;const filtered=(data.events||[]).filter(e=>(group==='ALL'||e.correlationId===group)&&(proto==='ALL'||e.protocol.indexOf(proto)>=0));setText('eventCount',filtered.length+' matching events');filtered.slice(0,90).forEach(e=>{const row=document.createElement('tr');row.className='clickable'+(selected===e.id?' selected':'');row.onclick=()=>{selected=e.id;selectEvent(e);renderEvents(last);};const route=td(e.from+' → '+e.to);const sub=document.createElement('div');sub.className='mono muted';sub.textContent=e.protocol;route.append(sub);const action=td(e.action);const corr=document.createElement('div');corr.className='mono muted';corr.textContent=shortId(e.correlationId);action.append(corr);const outcome=document.createElement('td');outcome.append(badge(e.outcome));row.append(td(fmtTime(e.time)),route,action,outcome);rows.append(row);});if(!filtered.length)rows.append(emptyRow(4,'No matching events. Clear filters or submit a new task.'));
 if(selected!=null){const event=(data.events||[]).find(e=>e.id===selected);if(event)selectEvent(event);else {selected=null;el('messageJson').textContent='Selected event expired from the bounded journal.';}}}
function selectEvent(event){const meta=el('messageMeta');meta.replaceChildren();[event.from+' → '+event.to,event.protocol,event.action,event.outcome,fmtTime(event.time),event.correlationId].forEach(str=>{const s=document.createElement('span');s.textContent=str;meta.append(s);});el('messageJson').textContent=JSON.stringify({timestamp:event.time,correlationId:event.correlationId,from:event.from,to:event.to,protocol:event.protocol,action:event.action,outcome:event.outcome,payload:event.payload},null,2);}
async function refresh(){if(refreshing)return;refreshing=true;try{const r=await fetch('/api/monitor/snapshot',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const data=await r.json();last=data;const status=el('connection');status.textContent='MONITOR CONNECTED';status.className='pill good';el('error').style.display='none';setText('updated','Updated '+fmtTime(data.generatedAt));setText('total',(data.tasks||[]).length);setText('complete',(data.tasks||[]).filter(t=>t.status==='COMPLETED').length);updateCorrelations(data.events||[]);renderPlc(data);renderTasks(data);renderEvents(data);}catch(err){el('connection').textContent='CONNECTION LOST';el('connection').className='pill bad';el('error').textContent='Cannot refresh WCS monitor: '+err.message+'. Displayed data may be stale.';el('error').style.display='block';}finally{refreshing=false;}}
el('refresh').onclick=refresh;el('correlation').onchange=()=>{selected=null;renderEvents(last);};el('protocol').onchange=()=>{selected=null;renderEvents(last);};el('clearSelection').onclick=()=>{el('correlation').value='ALL';el('protocol').value='ALL';selected=null;renderEvents(last);};el('copy').onclick=()=>{const text=el('messageJson').textContent;if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).catch(()=>{});}};
refresh();setInterval(refresh,2000);
})();
</script>
</body>
</html>
