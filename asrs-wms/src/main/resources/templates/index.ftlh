<#ftl output_format="HTML" auto_esc=true>
<#assign visibleTasks = tasks![]>
<#assign visibleInventory = inventory![]>
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASRS Control Center · WMS</title>
  <style>
    :root {color-scheme:light;--navy:#14253b;--navy2:#203a54;--ink:#1a2f44;--muted:#64758b;--blue:#235fb3;--line:#dce5ee;--bg:#f3f6fa;--green:#157045;--amber:#9a570e;--red:#ad3634}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;font-size:14px}
    header{background:linear-gradient(105deg,var(--navy),var(--navy2));color:white}
    .head{max-width:1240px;margin:auto;padding:24px 26px;display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
    .eyebrow{font-size:10px;letter-spacing:1.6px;text-transform:uppercase;font-weight:750;color:#8ebbe9}.brand{font-size:24px;font-weight:760;margin:3px 0}.subtitle{color:#c4d2e2;font-size:13px}
    .header-pill{border:1px solid #53708a;border-radius:999px;padding:8px 12px;color:#dfedfb;font-size:12px}
    main{max-width:1240px;margin:26px auto;padding:0 26px 30px}.intro{color:var(--muted);line-height:1.6;margin:0 0 20px}
    .stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}
    .stat,.panel{background:white;border:1px solid var(--line);border-radius:13px;box-shadow:0 3px 16px #112a4509}
    .stat{padding:18px 20px}.stat small{display:block;color:var(--muted);font-weight:600;font-size:12px}.stat strong{font-size:29px;display:block;line-height:1.3;margin-top:4px;font-variant-numeric:tabular-nums}
    .grid{display:grid;grid-template-columns:minmax(290px,340px) minmax(0,1fr);gap:18px;align-items:start}.panel{padding:22px;min-width:0}
    h2{font-size:17px;margin:0 0 9px}h3{font-size:14px;margin:0 0 8px}.muted,.hint{color:var(--muted);font-size:12px;line-height:1.55}
    label{display:block;font-size:12px;font-weight:750;margin:18px 0 7px}input,select{font:inherit;background:white;color:var(--ink);border:1px solid #b7c7d8;border-radius:8px;padding:11px 12px;width:100%}
    input:focus,select:focus,button:focus-visible{outline:3px solid #a8cbf3;outline-offset:1px}button{font:inherit;cursor:pointer}button.primary{border:0;border-radius:9px;background:var(--blue);color:white;font-weight:720;padding:12px 15px;width:100%;margin-top:18px}button.primary:hover{background:#1b4f97}
    .notice,.error,.sync-error{border-radius:9px;padding:11px 13px;margin-bottom:15px;font-size:13px}.notice{background:#e7f6ee;color:#145a36}.error,.sync-error{background:#fff0e8;color:#933c22}.sync-error{display:none}
    .separator{border:0;border-top:1px solid var(--line);margin:22px 0 17px}.locked{display:flex;gap:10px;align-items:start;border-radius:9px;background:#f5f7fb;padding:13px;color:var(--muted)}.locked strong{color:var(--ink)}
    .section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px}.section-head h2{margin-bottom:3px}
    .toolbar{display:flex;gap:8px;align-items:center;margin:13px 0 10px;flex-wrap:wrap}.toolbar input{flex:1 1 160px;max-width:300px}.toolbar select{width:auto;max-width:180px}
    button.secondary{border:1px solid var(--line);border-radius:8px;background:white;color:var(--ink);padding:10px 12px}
    .live{font-size:11px;color:var(--muted)}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:9px}table{width:100%;border-collapse:collapse;font-size:12px;text-align:left}th,td{padding:12px 10px;vertical-align:top}th{background:#f6f8fb;color:#566a7d;font-size:11px;white-space:nowrap}td{border-top:1px solid #e7edf3;line-height:1.45}td:nth-child(1){min-width:125px}td:nth-child(3){min-width:150px}.code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:11px;color:var(--muted)}
    .status{display:inline-block;padding:4px 9px;border-radius:99px;background:#e9f0ff;color:#244c82;font-weight:700;font-size:11px}.status.COMPLETED{background:#e4f5eb;color:var(--green)}.status.UNCERTAIN{background:#fff0d8;color:var(--amber)}.status.FAILED{background:#fee9e9;color:var(--red)}
    .inventory-panel{margin-top:18px}.inventory-panel table{max-width:720px}.steps{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.steps span{border:1px solid var(--line);padding:7px 10px;border-radius:7px;font-size:11px;color:#465b70}
    form[action="/retrieve"]{display:inline-flex;margin:0}form[action="/retrieve"] input[type="hidden"]{display:none}
    .footer-panel{margin-top:18px}.footer-panel p{margin-bottom:0}.empty{color:var(--muted);padding:20px 10px;text-align:center}
    @media(max-width:860px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:520px){main{padding:0 12px 20px}.head{padding:20px 14px}.panel{padding:15px}.stat{padding:13px}.brand{font-size:20px}.toolbar input,.toolbar select{max-width:none;flex:1 1 100%}}
    @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto}}

    /* v5 UX refresh — cohesive, self-contained; no external CSS/JS dependencies */
    :root { --navy:#10243e;--navy2:#1a3553;--ink:#182b43;--muted:#63758d;--blue:#225ec2;--line:#e0e8f2;--bg:#f4f7fb;--green:#127a51;--amber:#a45c0c;--red:#bb4545 }
    html { scroll-behavior:smooth }
    body { font-size:14px;letter-spacing:-.006em }
    header { background:linear-gradient(114deg,#11243c,#213f66);border-bottom:1px solid #294b71 }
    .head { max-width:1320px;padding:23px 30px }
    .eyebrow {color:#94c6ff}
    .brand {letter-spacing:-.035em;font-size:25px}
    .subtitle {color:#c4d7ec}
    .header-pill {background:rgba(255,255,255,.075);border-color:#52759c}
    main {max-width:1320px;padding:0 30px 50px}
    .intro {max-width:940px;margin-bottom:22px;font-size:13px}
    .stat,.panel {border-color:var(--line);border-radius:16px;box-shadow:0 8px 28px rgba(24,47,84,.035)}
    .stat {border-top:3px solid #dfe8f6;padding:16px 20px 17px}
    .stat:nth-child(2) {border-top-color:#81b0ff}
    .stat:nth-child(3) {border-top-color:#83cbb2}
    .stat:nth-child(4) {border-top-color:#f1c583}
    .stat small {font-size:12px}
    .stat strong {font-size:30px;letter-spacing:-.04em}
    .panel {padding:24px}
    h2 {font-size:18px;letter-spacing:-.025em;font-weight:760}
    h3 {font-size:14px}
    .grid {grid-template-columns:minmax(285px,350px) minmax(0,1fr)}
    .toolbar input {max-width:none}
    .table-wrap {border-radius:11px;border-color:#dfe7f1}
    table {font-size:13px}
    th {padding:14px 15px;background:#f6f8fc;color:#62738a;font-weight:760}
    td {padding:15px;line-height:1.5;border-top-color:#edf1f6}
    tbody tr:hover {background:#fafcff}
    .code {font-size:11px}
    .status {font-size:10px;letter-spacing:.025em}
    button.secondary {font-weight:650;background:#fff;border:1px solid #c8d8ec;color:#234e83}
    button.secondary:hover {background:#eff5ff;border-color:#99b8e8}
    button:disabled {opacity:.6;cursor:wait}
    .section-head {margin-bottom:16px}
    .section-head h2 {margin-bottom:6px}
    .live {background:#f4f8ff;border:1px solid #e2ebf8;border-radius:7px;padding:7px 10px}
    [hidden] {display:none!important}

    /* Confirmed inventory — roomy, searchable, and informative when empty */
    .inventory-panel {margin-top:20px;padding:26px 28px 28px}
    .inventory-panel table {max-width:none;width:100%}
    .section-kicker {display:flex;align-items:center;gap:8px;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;font-weight:800;color:#5276a0;margin-bottom:8px}
    .section-kicker .mark {height:7px;width:7px;border-radius:50%;background:#2c75dc;box-shadow:0 0 0 4px #eaf2ff}
    .section-title-row {display:flex;align-items:center;gap:12px;flex-wrap:wrap}
    .inventory-panel .section-head {margin-bottom:19px}
    .inventory-panel h2 {font-size:20px;letter-spacing:-.03em;margin:0}
    .count-pill {background:#e9f2ff;border:1px solid #d9e7ff;border-radius:999px;color:#27558e;display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:760;padding:7px 12px;white-space:nowrap}
    .count-pill::before {content:'';width:7px;height:7px;background:#3a83d9;border-radius:50%}
    .inventory-helper {display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:8px;color:var(--muted);font-size:12px;line-height:1.65}
    .inventory-helper .dot {color:#b9c7da}
    .inventory-toolbar {display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}
    .inventory-toolbar .search-wrap {position:relative;max-width:390px;flex:1 1 260px}
    .inventory-toolbar .search-wrap svg {position:absolute;top:50%;left:13px;transform:translateY(-50%);color:#7790a9;pointer-events:none}
    .inventory-toolbar input {border-radius:9px;padding-left:40px;background:#fcfdff;border-color:#d8e3ef}
    .inventory-toolbar .toolbar-meta {display:flex;align-items:center;gap:12px}
    .inventory-toolbar .table-note {color:var(--muted);font-size:12px}
    .inventory-wrap {overflow:auto}
    .inventory-wrap th:nth-child(1) {width:26%}
    .inventory-wrap th:nth-child(2) {width:21%}
    .inventory-wrap th:nth-child(3) {width:38%}
    .inventory-wrap th:nth-child(4) {width:15%}
    .inventory-wrap td:nth-child(3) {min-width:170px}
    .inventory-wrap td:nth-child(1) {min-width:120px}
    .inventory-id {display:flex;align-items:center;gap:10px;color:#213b5a;font-weight:750}
    .pallet-icon {background:#edf4ff;border-radius:9px;width:34px;height:34px;display:inline-grid;place-items:center;flex:0 0 auto;color:#3569b2}
    .rack-location {font:750 13px ui-monospace,SFMono-Regular,Consolas,monospace;color:#244f84}
    .inventory-retrieve {display:inline-flex;align-items:center;gap:6px;white-space:nowrap;padding:8px 12px!important}
    .inventory-retrieve::after {content:'↗';font-size:14px}
    .inventory-empty {display:grid;grid-template-columns:170px minmax(0,1fr);gap:26px;align-items:center;padding:34px 36px;border-radius:14px;border:1px dashed #c8d9ed;background:linear-gradient(100deg,#f7faff,#ffffff 64%)}
    .empty-illustration {display:grid;place-items:center;height:134px;border-radius:14px;background:radial-gradient(circle at 45% 50%,#e2edff,#f0f5fc 73%);color:#5080bb}
    .inventory-empty h3 {font-size:18px;letter-spacing:-.025em;margin:0 0 8px;color:#193b60}
    .inventory-empty p {font-size:13px;line-height:1.7;color:var(--muted);max-width:550px;margin:0 0 18px}
    .link-action {display:inline-flex;gap:8px;align-items:center;text-decoration:none;background:var(--blue);border:1px solid var(--blue);color:#fff;border-radius:9px;padding:10px 14px;font-weight:740;font-size:12px}
    .link-action:hover {background:#164eac}
    .subtle-meta {margin-top:14px;display:flex;align-items:center;gap:8px;color:#7589a1;font-size:11px}
    .subtle-meta svg {flex:0 0 auto}

    /* Network architecture — visual directions, not live connection health */
    .architecture-panel {margin-top:20px;padding:27px 28px 24px}
    .architecture-heading {display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:23px}
    .architecture-heading h2 {font-size:20px;letter-spacing:-.03em;margin-bottom:8px}
    .architecture-heading .muted {max-width:715px;font-size:12px}
    .monitor-button {display:inline-flex;align-items:center;gap:9px;text-decoration:none;border-radius:10px;border:1px solid #bfd4ef;background:#f0f6ff;color:#24508a;font-size:12px;font-weight:760;padding:12px 14px;white-space:nowrap}
    .monitor-button:hover {background:#e5efff;border-color:#9dbce8}
    .architecture-board {border:1px solid #e1eaf4;background:linear-gradient(180deg,#f7faff 0%,#fff 76%);border-radius:14px;padding:22px}
    .arch-main {display:grid;grid-template-columns:minmax(0,1fr) 190px minmax(0,1fr);align-items:center;gap:13px;max-width:930px;margin:0 auto}
    .arch-node {position:relative;background:#fff;border:1px solid #d8e4f2;border-radius:12px;padding:18px 20px;box-shadow:0 6px 18px rgba(34,68,112,.04);min-height:128px}
    .arch-node .node-tag {font-size:10px;letter-spacing:1.2px;color:#6a86a5;font-weight:800;text-transform:uppercase;margin-bottom:8px}
    .arch-node h3 {font-size:17px;letter-spacing:-.025em;margin-bottom:5px}
    .arch-node p {font-size:12px;color:#667b91;line-height:1.55;margin:0}
    .arch-node .port {position:absolute;right:15px;top:14px;font:750 11px ui-monospace,SFMono-Regular,Consolas,monospace;background:#f0f4fa;color:#526f8c;padding:5px 7px;border-radius:6px}
    .arch-node.wcs {border:1.5px solid #72a4e7;background:#edf5ff;box-shadow:0 8px 23px rgba(36,111,203,.1)}
    .arch-node.wcs .node-tag {color:#1d63b3}
    .arch-node.wcs h3 {color:#174a83}
    .arch-direction {text-align:center;display:grid;justify-items:center;gap:8px;color:#4d6a8c}
    .arch-direction .protocol {font-size:11px;font-weight:760;color:#2c5e9b;background:#e6f0ff;padding:6px 10px;border-radius:999px}
    .arch-direction .arrowline {height:2px;width:95%;background:linear-gradient(90deg,#b5cce8,#4086d8);position:relative}
    .arch-direction .arrowline::after {content:'';position:absolute;right:-1px;top:-4px;border-top:5px solid transparent;border-bottom:5px solid transparent;border-left:7px solid #4086d8}
    .arch-direction small {font-size:11px;color:#7690ab}
    .branch-head {display:flex;align-items:center;gap:12px;margin:22px 0 13px;color:#7387a1;font-size:10px;letter-spacing:1.15px;font-weight:780;text-transform:uppercase}
    .branch-head::before,.branch-head::after {content:'';height:1px;background:#dce7f3;flex:1}
    .arch-branches {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}
    .branch {background:#fff;border:1px solid #e0e8f2;border-radius:11px;padding:17px;min-width:0;position:relative}
    .branch::before {content:'';position:absolute;top:-1px;left:17px;width:38px;height:3px;border-radius:4px;background:#75a7e1}
    .branch.plc::before {background:#65b6a3}
    .branch.gazebo::before {background:#a998dc}
    .branch .branch-label {display:inline-flex;align-items:center;gap:7px;font-size:10px;letter-spacing:.7px;font-weight:800;text-transform:uppercase;color:#607d9e;margin-bottom:12px}
    .branch .branch-label span {background:#eff5ff;color:#346bb0;border-radius:5px;padding:4px 6px;font:750 10px ui-monospace,SFMono-Regular,Consolas,monospace}
    .branch h3 {font-size:15px;margin:0 0 6px;color:#233f60}
    .branch p {font-size:12px;color:#60758e;line-height:1.6;margin:0}
    .branch .examples {margin-top:11px;background:#f5f8fd;border-radius:7px;padding:9px 10px;color:#46627e;line-height:1.65;font:500 11px ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}
    .interface-details {margin-top:16px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
    .payload-card {border:1px solid #dfe8f3;border-radius:10px;background:#fff;min-width:0;overflow:hidden}
    .payload-card summary {cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px;padding:13px 16px;font-size:12px;font-weight:740;color:#3d5a78;list-style:none}
    .payload-card summary::-webkit-details-marker {display:none}
    .payload-card summary::after {content:'+';font-size:18px;color:#6690be}
    .payload-card[open] summary::after {content:'−'}
    .payload-card pre {white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:auto;font-size:11px;line-height:1.7;background:#0e223c;color:#d8e9fa;padding:15px 16px;margin:0}
    .architecture-disclaimer {display:flex;gap:12px;align-items:flex-start;border-top:1px solid #e5edf6;margin-top:20px;padding-top:16px;font-size:12px;color:#6a7d92;line-height:1.65}
    .architecture-disclaimer svg {flex:0 0 auto;color:#809ab8;margin-top:1px}
    .architecture-disclaimer strong {color:#3d5472}
    @media(max-width:860px) {.grid{grid-template-columns:1fr}}
    @media(max-width:1050px) {.arch-main {grid-template-columns:minmax(0,1fr) 120px minmax(0,1fr)}.arch-branches {gap:10px}.inventory-empty {grid-template-columns:128px minmax(0,1fr);padding:26px}}
    @media(max-width:800px) {.arch-branches {grid-template-columns:1fr}.branch{padding:15px}.arch-main{grid-template-columns:minmax(0,1fr) 85px minmax(0,1fr)}.arch-direction small{display:none}.inventory-panel,.architecture-panel{padding:20px}.interface-details{grid-template-columns:1fr}}
    @media(max-width:600px) {main{padding:0 14px 36px}.arch-main{grid-template-columns:1fr;gap:10px}.arch-direction .arrowline{width:2px;height:34px;background:linear-gradient(#b5cce8,#4086d8)}.arch-direction .arrowline::after{right:-4px;top:auto;bottom:-1px;border-top:7px solid #4086d8;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:0}.arch-direction small{display:block}.inventory-empty{grid-template-columns:1fr;text-align:center;justify-items:center;padding:23px}.empty-illustration{width:100%;max-width:180px}.architecture-board{padding:14px}.inventory-panel,.architecture-panel{padding:18px}.inventory-toolbar .table-note{display:none}}
  </style>
</head>
<body>
<header><div class="head"><div><div class="eyebrow">Operations lab · Digital twin</div><div class="brand">ASRS Control Center</div><div class="subtitle">Warehouse Management System · Kotlin / Spring Boot / FreeMarker</div></div><div class="header-pill">Simulation environment · No physical motion control</div></div></header>
<main>
  <p class="intro">Create putaway tasks and monitor WCS/virtual PLC acknowledgements. Confirmed inventory appears only when WCS verifies the PLC completion and destination. Gazebo displays movements separately.</p>
  <#if notice??><div class="notice" role="status">${notice}</div></#if>
  <#if error??><div class="error" role="alert">${error}</div></#if>
  <div class="sync-error" id="syncError" role="alert">Live task refresh temporarily unavailable. Previously displayed information may be stale.</div>
  <section class="stats" aria-label="Warehouse task summary">
    <div class="stat"><small>Total tasks</small><strong id="statTotal">${visibleTasks?size}</strong></div>
    <div class="stat"><small>Active tasks</small><strong id="statActive">${activeCount!0}</strong></div>
    <div class="stat"><small>Completed</small><strong id="statCompleted">${completedCount!0}</strong></div>
    <div class="stat"><small>Uncertain / needs review</small><strong id="statUncertain">${uncertainCount!0}</strong></div>
  </section>
  <section class="grid">
    <div class="panel">
      <h2>New putaway task</h2><p class="muted">Send a new pallet to an unused demo rack location. Existing pallet IDs and reserved rack locations are blocked to prevent accidental duplicate commands.</p>
      <form method="post" action="/putaway" id="putawayForm">
        <label for="palletId">Pallet ID</label>
        <input id="palletId" name="palletId" autocomplete="off" placeholder="e.g. P007" required maxlength="40" pattern="[A-Za-z0-9_-]+">
        <label for="targetLocation">Storage destination</label>
        <input id="targetLocation" name="targetLocation" autocomplete="off" placeholder="e.g. A-02-01" required maxlength="7" pattern="A-[0-9]{2}-[0-9]{2}" style="text-transform:uppercase">
        <p class="hint">Visible rack range: A-01-01 to A-06-04. Use a new pallet ID for each test.</p>
        <button class="primary" type="submit">Submit putaway to WCS</button>
      </form>
      <hr class="separator">
      <h3>Retrieval workflow</h3>
      <p class="hint">Retrieve a confirmed pallet using the button in the inventory table below. The pallet remains stored until WCS confirms outbound release.</p>
      <div class="locked"><span aria-hidden="true">ℹ</span><div><strong>Simulation-only retrieval</strong><div class="hint">The virtual PLC travels to the source rack, simulates pickup, then returns to the outbound handoff. Gazebo shows a simplified transfer.</div></div></div>
    </div>
    <div class="panel">
      <div class="section-head"><div><h2>Warehouse tasks</h2><div class="muted">Auto-refreshes every 2 seconds without resetting your form.</div></div><div class="live" id="lastUpdated" role="status">Connecting to local WMS API…</div></div>
      <div class="toolbar"><input id="taskSearch" type="search" placeholder="Search pallet, rack or task ID" aria-label="Search warehouse tasks"><select id="taskFilter" aria-label="Filter tasks by status"><option value="ALL">All statuses</option><option value="ACTIVE">Active</option><option value="COMPLETED">Completed</option><option value="UNCERTAIN">Uncertain</option></select><button class="secondary" type="button" id="refreshNow">Refresh</button></div>
      <div class="table-wrap"><table><thead><tr><th>Pallet / task</th><th>Rack / operation</th><th>State</th><th>Confirmed location</th><th>PLC cmd</th></tr></thead><tbody id="taskRows">
      <#if visibleTasks?size == 0>
        <tr><td colspan="5" class="empty">No tasks yet. Submit a putaway to begin.</td></tr>
      <#else>
        <#list visibleTasks as task>
          <tr><td><strong>${task.palletId}</strong><div class="code" title="${task.wmsTaskId}">${task.wmsTaskId?keep_before_last('-')}…</div></td><td>${task.targetLocation}<div class="code">${task.operation!"PUTAWAY"}</div></td><td><span class="status ${task.status}">${task.status}</span><div class="muted">${task.detail}</div></td><td>${task.storedLocation!"Not confirmed"}</td><td>${(task.commandId?c)!"—"}</td></tr>
        </#list>
      </#if>
      </tbody></table></div>
    </div>
  </section>

  <section class="panel inventory-panel" aria-labelledby="inventoryTitle" id="confirmedInventory">
    <div class="section-head">
      <div>
        <div class="section-kicker"><span class="mark"></span> Warehouse stock</div>
        <div class="section-title-row">
          <h2 id="inventoryTitle">Confirmed inventory</h2>
          <span class="count-pill" id="inventoryCount" aria-live="polite">${visibleInventory?size} pallet(s)</span>
        </div>
        <div class="inventory-helper">
          <span>Added after verified putaway</span><span class="dot">·</span>
          <span>Removed after verified retrieval</span><span class="dot">·</span>
          <span>Demo data stored in memory</span>
        </div>
      </div>
    </div>

    <div class="inventory-empty" id="inventoryEmpty" <#if visibleInventory?size != 0>hidden</#if>>
      <div class="empty-illustration" aria-hidden="true">
        <svg width="124" height="104" viewBox="0 0 124 104" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 85H107" stroke="#B5CAE4" stroke-width="3" stroke-linecap="round"/>
          <path d="M28 18V84M62 18V84M96 18V84M24 18H100M24 49H100M24 84H100" stroke="#6C94C4" stroke-width="5" stroke-linecap="round"/>
          <path d="M34 29H55V43H34V29ZM68 29H89V43H68V29ZM34 60H55V74H34V60Z" fill="#C6D8EE" stroke="#88AED8" stroke-width="2"/>
          <path d="M70 61L78 69L91 55" stroke="#3278CB" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div>
        <h3>No pallets stored yet</h3>
        <p>Confirmed inventory appears here after a putaway command is accepted and completed by the virtual PLC. Start with a new pallet and an available rack location.</p>
        <a class="link-action" href="#putawayForm">Create your first putaway <span aria-hidden="true">→</span></a>
      </div>
    </div>

    <div class="inventory-toolbar" id="inventoryToolbar" <#if visibleInventory?size == 0>hidden</#if>>
      <div class="search-wrap">
        <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
        <input id="inventorySearch" type="search" placeholder="Search pallets or rack locations" aria-label="Search confirmed inventory">
      </div>
      <div class="toolbar-meta"><span class="table-note">Verified stock only</span><button class="secondary" type="button" id="exportInventory">Export CSV</button></div>
    </div>
    <div class="table-wrap inventory-wrap" id="inventoryTableWrap" <#if visibleInventory?size == 0>hidden</#if>>
      <table aria-label="Confirmed pallets currently in warehouse">
        <thead><tr><th>Pallet</th><th>Storage location</th><th>Verified WMS task</th><th>Operation</th></tr></thead>
        <tbody id="inventoryRows">
          <#list visibleInventory as item>
            <tr>
              <td><div class="inventory-id"><span class="pallet-icon" aria-hidden="true">▣</span><strong>${item.palletId}</strong></div></td>
              <td><span class="rack-location">${item.location}</span></td>
              <td class="code" title="${item.sourceTaskId}">${item.sourceTaskId}</td>
              <td><form method="post" action="/retrieve"><input type="hidden" name="palletId" value="${item.palletId}"><button type="submit" class="secondary inventory-retrieve">Retrieve</button></form></td>
            </tr>
          </#list>
        </tbody>
      </table>
    </div>
    <div class="subtle-meta"><svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/></svg> Warehouse stock is confirmed by WCS/PLC feedback. Gazebo is a visualization, not inventory authority.</div>
  </section>

  <section class="panel architecture-panel" aria-labelledby="architectureTitle" id="systemFlow">
    <div class="architecture-heading">
      <div>
        <div class="section-kicker"><span class="mark"></span> System communication</div>
        <h2 id="architectureTitle">How a warehouse task moves through the system</h2>
        <p class="muted">Trace the request from WMS to WCS, then the planning, execution and visual feedback paths. These labels describe interfaces—not live connectivity checks.</p>
      </div>
      <a class="monitor-button" href="http://localhost:8080/monitor" target="_blank" rel="noopener noreferrer">Open WCS message monitor <span aria-hidden="true">↗</span></a>
    </div>
    <div class="architecture-board">
      <div class="arch-main">
        <article class="arch-node">
          <span class="port">:8081</span>
          <div class="node-tag">01 · Warehouse request</div>
          <h3>WMS</h3>
          <p>Creates putaway or retrieval tasks; updates inventory after verified completion.</p>
        </article>
        <div class="arch-direction" aria-label="WMS sends REST JSON tasks to WCS">
          <span class="protocol">REST · JSON</span>
          <div class="arrowline"></div>
          <small>POST /api/tasks</small>
        </div>
        <article class="arch-node wcs">
          <span class="port">:8080</span>
          <div class="node-tag">02 · Command orchestration</div>
          <h3>WCS</h3>
          <p>Validates requests, assigns command IDs, coordinates execution and verifies feedback.</p>
        </article>
      </div>
      <div class="branch-head">WCS coordinates these three interfaces</div>
      <div class="arch-branches">
        <article class="branch ros">
          <div class="branch-label"><span>HTTP</span> Planning request ↔ result</div>
          <h3>ROS 2 planner <span class="code">:8091</span></h3>
          <p>Checks target rack and returns the calculated X/Z position. Planning is advisory.</p>
          <div class="examples">POST /plan<br>target → xMm, zMm, valid</div>
        </article>
        <article class="branch plc">
          <div class="branch-label"><span>OPC UA</span> Writes ↔ feedback</div>
          <h3>Virtual PLC <span class="code">:12686</span></h3>
          <p>Receives location, operation and command ID; exposes acceptance, machine state and completion.</p>
          <div class="examples">TargetLocation<br>CommandOperation<br>CommandId → AcceptedCommandId</div>
        </article>
        <article class="branch gazebo">
          <div class="branch-label"><span>ROS 2</span> Read-only visualization</div>
          <h3>Gazebo digital twin</h3>
          <p>A visual adapter reads WCS/PLC feedback and publishes crane and pallet animation updates.</p>
          <div class="examples">WCS status → visual adapter<br>ROS topics → Gazebo scene</div>
        </article>
      </div>
      <div class="interface-details" aria-label="Examples of messages and machine feedback">
        <details class="payload-card">
          <summary>Example incoming WMS request</summary>
          <pre>{
  "palletId": "P-001",
  "targetLocation": "A-02-01",
  "externalTaskId": "WMS-example-01"
}</pre>
        </details>
        <details class="payload-card">
          <summary>Example PLC writes and feedback</summary>
          <pre>WRITE TargetLocation = A-02-01
WRITE CommandOperation = PUTAWAY
WRITE CommandId = 5

READ AcceptedCommandId = 5
READ MachineState = COMPLETED
READ CompletedCommandId = 5</pre>
        </details>
      </div>
    </div>
    <div class="architecture-disclaimer">
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/></svg>
      <div><strong>Simulation environment.</strong> Tasks and inventory currently live in memory. Restarting WMS or WCS can lose its local ledger and requires reconciliation. A real installation needs persistent inventory, authentication, equipment interlocks and independently engineered machine safety.</div>
    </div>
  </section>
</main>
<script>
(() => {
  const q = id => document.getElementById(id);
  const taskRows = q('taskRows');
  const inventoryRows = q('inventoryRows');
  let taskCache = [];
  let stockCache = [];
  let refreshing = false;

  const cell = (text, className = '') => {
    const td = document.createElement('td');
    if (className) td.className = className;
    td.textContent = String(text ?? '');
    return td;
  };
  const empty = (message, cols) => {
    const tr = document.createElement('tr');
    const td = cell(message, 'empty');
    td.colSpan = cols;
    tr.append(td);
    return tr;
  };

  function renderTasks() {
    const search = q('taskSearch').value.trim().toLowerCase();
    const filter = q('taskFilter').value;
    const filtered = taskCache.filter(t => {
      const match = [t.palletId, t.targetLocation, t.operation, t.wmsTaskId, t.wcsTaskId, t.status]
        .some(value => String(value ?? '').toLowerCase().includes(search));
      const matchStatus = filter === 'ALL' || t.status === filter ||
        (filter === 'ACTIVE' && ['SUBMITTING','ACCEPTED','RUNNING'].includes(t.status));
      return match && matchStatus;
    });
    const rows = filtered.map(t => {
      const tr = document.createElement('tr');
      const first = document.createElement('td');
      const strong = document.createElement('strong');
      strong.textContent = String(t.palletId ?? '');
      const sub = document.createElement('div');
      sub.className = 'code';
      sub.title = String(t.wmsTaskId ?? '');
      sub.textContent = String(t.wmsTaskId ?? '').slice(0, 20) + '…';
      first.append(strong, sub);
      const state = document.createElement('td');
      const badge = document.createElement('span');
      const safeStatus = ['COMPLETED','UNCERTAIN','FAILED','SUBMITTING','ACCEPTED','RUNNING'].includes(t.status)
        ? t.status : 'UNKNOWN';
      badge.className = 'status ' + safeStatus;
      badge.textContent = safeStatus;
      const detail = document.createElement('div');
      detail.className = 'muted';
      detail.textContent = String(t.detail ?? '');
      state.append(badge, detail);
      const rack = document.createElement('td');
      rack.append(document.createTextNode(String(t.targetLocation ?? '')));
      const operation = document.createElement('div');
      operation.className = 'code';
      operation.textContent = String(t.operation ?? 'PUTAWAY');
      rack.append(operation);
      tr.append(first, rack, state,
        cell(t.storedLocation || 'Not confirmed'), cell(t.commandId ?? '—'));
      return tr;
    });
    taskRows.replaceChildren(...(rows.length ? rows : [empty('No tasks match this filter.', 5)]));
    q('statTotal').textContent = String(taskCache.length);
    q('statActive').textContent = String(taskCache.filter(t => ['SUBMITTING','ACCEPTED','RUNNING'].includes(t.status)).length);
    q('statCompleted').textContent = String(taskCache.filter(t => t.status === 'COMPLETED').length);
    q('statUncertain').textContent = String(taskCache.filter(t => t.status === 'UNCERTAIN').length);
  }

  function renderInventory(stock) {
    stockCache = stock;
    const hasStock = stock.length > 0;
    q('inventoryCount').textContent = stock.length + ' pallet' + (stock.length === 1 ? '' : 's');
    q('inventoryEmpty').hidden = hasStock;
    q('inventoryToolbar').hidden = !hasStock;
    q('inventoryTableWrap').hidden = !hasStock;
    if (!hasStock) {
      inventoryRows.replaceChildren();
      return;
    }
    const query = q('inventorySearch').value.trim().toLowerCase();
    const visible = stock.filter(item =>
      [item.palletId, item.location, item.sourceTaskId]
        .some(value => String(value ?? '').toLowerCase().includes(query)));
    const rows = visible.map(item => {
      const tr = document.createElement('tr');
      const first = document.createElement('td');
      const identity = document.createElement('div');
      identity.className = 'inventory-id';
      const pictogram = document.createElement('span');
      pictogram.className = 'pallet-icon';
      pictogram.textContent = '▣';
      pictogram.setAttribute('aria-hidden', 'true');
      const name = document.createElement('strong');
      name.textContent = String(item.palletId ?? '');
      identity.append(pictogram, name);
      first.append(identity);
      const rack = document.createElement('td');
      const code = document.createElement('span');
      code.className = 'rack-location';
      code.textContent = String(item.location ?? '');
      rack.append(code);
      const action = document.createElement('td');
      const form = document.createElement('form');
      form.method = 'post';
      form.action = '/retrieve';
      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'palletId';
      hidden.value = String(item.palletId ?? '');
      const button = document.createElement('button');
      button.type = 'submit';
      button.className = 'secondary inventory-retrieve';
      button.textContent = 'Retrieve';
      form.append(hidden, button);
      action.append(form);
      tr.append(first, rack, cell(item.sourceTaskId, 'code'), action);
      return tr;
    });
    inventoryRows.replaceChildren(...(rows.length ? rows : [empty('No pallets match your search.', 4)]));
  }

  function exportInventoryCSV() {
    if (!stockCache.length) return;
    const csvCell = value => {
      const raw = String(value ?? '');
      const safe = /^[=+\-@\t\r]/.test(raw) ? '\'' + raw : raw;
      return '"' + safe.replace(/"/g, '""') + '"';
    };
    const rows = [
      ['Pallet ID','Confirmed rack','WMS source task'],
      ...stockCache.map(item => [item.palletId, item.location, item.sourceTaskId])
    ];
    const csv = rows.map(row => row.map(csvCell).join(',')).join('\r\n');
    const blob = new Blob(['\uFEFF',csv], {type:'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'asrs-confirmed-inventory.csv';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function getJSON(path) {
    const response = await fetch(path, {cache:'no-store', headers:{'Accept':'application/json'}});
    if (!response.ok) throw new Error('HTTP ' + response.status + ' at ' + path);
    return response.json();
  }
  async function refresh() {
    if (refreshing || document.visibilityState === 'hidden') return;
    refreshing = true;
    try {
      const [tasks, stock] = await Promise.all([
        getJSON('/api/wms/tasks'), getJSON('/api/wms/inventory')
      ]);
      if (!Array.isArray(tasks) || !Array.isArray(stock)) throw new Error('Unexpected API result');
      taskCache = tasks;
      renderTasks();
      renderInventory(stock);
      q('syncError').style.display = 'none';
      q('lastUpdated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    } catch (e) {
      q('syncError').style.display = 'block';
      q('lastUpdated').textContent = 'Live sync unavailable';
      console.warn('ASRS dashboard refresh failed:', e);
    } finally {
      refreshing = false;
    }
  }
  q('inventorySearch').addEventListener('input', () => renderInventory(stockCache));
  q('exportInventory').addEventListener('click', exportInventoryCSV);
  q('taskSearch').addEventListener('input', renderTasks);
  q('taskFilter').addEventListener('change', renderTasks);
  q('refreshNow').addEventListener('click', refresh);
  q('putawayForm').addEventListener('submit', () => {
    q('putawayForm').querySelector('button[type="submit"]').disabled = true;
  });
  refresh();
  setInterval(refresh, 2000);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refresh();
  });
})();
</script>
</body>
</html>
