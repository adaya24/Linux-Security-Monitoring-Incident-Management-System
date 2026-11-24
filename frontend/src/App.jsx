
import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import "./App.css";

const pages = [
  ["dashboard", "▦", "Dashboard"],
  ["processes", "⌘", "Processes"],
  ["events", "◉", "Security Events"],
  ["audits", "⌕", "Security Audit"],
  ["incidents", "▤", "Incidents"],
];

function Badge({ value }) {
  const text = String(value || "UNKNOWN");
  const css = text.toLowerCase().replaceAll("_", "-");
  return <span className={`badge badge-${css}`}>{text.replaceAll("_", " ")}</span>;
}

function Panel({ title, subtitle, children, action }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function Table({ columns, rows, empty = "No records available." }) {
  return (
    <>
      <div className="table-wrap">
        <table>
          <thead><tr>{columns.map((col) => <th key={col}>{col}</th>)}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      {!rows.length && <div className="empty-state">{empty}</div>}
    </>
  );
}

function dateText(value) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [processes, setProcesses] = useState([]);
  const [events, setEvents] = useState([]);
  const [audits, setAudits] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [assignmentDrafts, setAssignmentDrafts] = useState({});
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [updatedAt, setUpdatedAt] = useState(null);

  const refresh = useCallback(async () => {
    const jobs = [
      ["Processes", api.getProcesses, setProcesses],
      ["Security events", api.getEvents, setEvents],
      ["Audit results", api.getAuditResults, setAudits],
      ["Incidents", api.getIncidents, setIncidents],
    ];

    const failed = [];
    await Promise.all(jobs.map(async ([label, fn, setter]) => {
      try {
        const result = await fn();
        setter(Array.isArray(result) ? result : []);
      } catch (error) {
        failed.push(`${label}: ${error.message}`);
      }
    }));

    setErrors(failed);
    setUpdatedAt(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 10000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function runAction(action, successMessage) {
    setBusy(true);
    setNotice("");
    try {
      const result = await action();
      setNotice(typeof successMessage === "function" ? successMessage(result) : successMessage);
      await refresh();
    } catch (error) {
      setNotice(`Action failed: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  const activePage = pages.find((item) => item[0] === page)?.[2] || "Dashboard";
  const openIncidents = incidents.filter((i) => ["OPEN", "INVESTIGATING"].includes(i.status)).length;
  const criticalEvents = events.filter((e) => ["HIGH", "EXTREME_HIGH"].includes(e.severity)).length;
  const filteredProcesses = processes.filter((p) =>
    `${p.pid} ${p.name} ${p.username} ${p.status}`.toLowerCase().includes(search.toLowerCase())
  );

  const processRows = filteredProcesses
    .slice()
    .sort((a, b) => Number(b.memory_mb || 0) - Number(a.memory_mb || 0))
    .map((p) => (
      <tr key={p.pid}>
        <td>{p.pid}</td><td><strong>{p.name}</strong></td><td>{p.username}</td>
        <td>{p.status}</td><td>{Number(p.cpu_percent || 0).toFixed(1)}%</td>
        <td>{Number(p.memory_mb || 0).toFixed(2)} MB</td>
      </tr>
    ));

  const eventRows = events.map((e, index) => (
    <tr key={e.id ?? index}>
      <td>{e.id ?? "—"}</td>
      <td><strong>{e.event_type || "Security event"}</strong><small>{e.description}</small></td>
      <td><Badge value={e.severity} /></td><td>{e.pid ?? "—"}</td>
      <td>{dateText(e.created_at || e.recorded_at)}</td>
    </tr>
  ));

  const auditRows = audits.map((a) => (
    <tr key={a.audit_id}>
      <td><strong>{a.check_type}</strong></td><td><Badge value={a.status} /></td>
      <td><Badge value={a.severity} /></td><td>{a.description}</td>
      <td>{dateText(a.checked_at)}</td>
    </tr>
  ));

  const incidentRows = incidents.map((i) => (
  <tr key={i.incident_id}>
    <td>{i.incident_id}</td>
    <td><strong>{i.title}</strong><small>{i.description}</small></td>
    <td><Badge value={i.severity} /></td>
    <td><Badge value={i.status} /></td>
    <td>
      <div style={{ display: "flex", gap: "6px", minWidth: "180px" }}>
        <input
          value={assignmentDrafts[i.incident_id] ?? i.assigned_to ?? ""}
          placeholder="Enter analyst name"
          onChange={(e) =>
            setAssignmentDrafts((prev) => ({
              ...prev,
              [i.incident_id]: e.target.value,
            }))
          }
        />
        <button
          className="secondary-button"
          disabled={busy}
          onClick={() =>
            runAction(
              () =>
                api.updateIncident(
                  i.incident_id,
                  i.status,
                  assignmentDrafts[i.incident_id] ?? i.assigned_to ?? null
                ),
              `Incident #${i.incident_id} assigned successfully.`
            )
          }
        >
          Save
        </button>
      </div>
    </td>
    <td>
      <select
        value={i.status}
        aria-label={`Status for incident ${i.incident_id}`}
        onChange={(e) =>
          runAction(
            () => api.updateIncident(i.incident_id, e.target.value, i.assigned_to),
            `Incident #${i.incident_id} updated.`
          )
        }
      >
        {["OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"].map((s) =>
          <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
        )}
      </select>
    </td>
  </tr>
));
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">R</div>
          <div><strong>RootShield</strong><small>LINUX SECURITY MONITOR</small></div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav>
          {pages.map(([id, icon, label]) => (
            <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => setPage(id)}>
              <span className="nav-icon">{icon}</span><span>{label}</span>
              {id === "events" && events.length > 0 && <span className="nav-count">{events.length}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span className={`status-dot ${errors.length ? "offline" : ""}`} />
            <div><strong>Backend connection</strong><small>{loading ? "Connecting…" : errors.length ? "Needs attention" : "API reachable"}</small></div>
          </div>
          <small className="sidebar-version">RootShield · Development</small>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> <strong>{activePage}</strong></div>
          <div className="topbar-right">
            <span className="environment-tag">KALI LINUX</span>
            <button className="refresh-button" title="Refresh data" onClick={refresh}>↻</button>
          </div>
        </header>

        <div className="page-content">
          {errors.length > 0 && (
            <div className="alert-box error-box">
              <strong>Some API requests failed</strong>
              {errors.map((e) => <div key={e}>{e}</div>)}
              <span>Confirm that FastAPI is running on port 8001 and CORS is configured.</span>
            </div>
          )}
          {notice && <div className="alert-box notice-box">{notice}<button onClick={() => setNotice("")}>×</button></div>}
          {loading && <div className="loading-strip">Loading system information…</div>}

          {page === "dashboard" && (
            <>
              <div className="page-heading">
                <div><div className="eyebrow">SYSTEM OVERVIEW</div><h1>Security Dashboard</h1>
                  <p>Monitor processes, investigate events, and review system security.</p></div>
                <div className="system-pill"><span className="status-dot" /> Monitoring API</div>
              </div>

              <div className="metric-grid">
                <article className="metric-card"><div className="metric-icon teal">⌘</div><span>Processes</span><strong>{processes.length}</strong><small>Returned by the API</small></article>
                <article className="metric-card"><div className="metric-icon amber">◉</div><span>Security events</span><strong>{events.length}</strong><small>{criticalEvents} high / extreme-high</small></article>
                <article className="metric-card"><div className="metric-icon blue">⌕</div><span>Audit findings</span><strong>{audits.length}</strong><small>Saved audit results</small></article>
                <article className="metric-card"><div className="metric-icon purple">▤</div><span>Open incidents</span><strong>{openIncidents}</strong><small>Open or investigating</small></article>
              </div>

              <div className="content-grid">
                <Panel title="Recent Security Events" subtitle="Latest detection records" action={<button className="text-button" onClick={() => setPage("events")}>View all →</button>}>
                  <Table columns={["Event", "Severity", "PID"]} rows={events.slice(0, 5).map((e, index) =>
                    <tr key={e.id ?? index}><td><strong>{e.event_type || "Security event"}</strong><small>{e.description}</small></td><td><Badge value={e.severity} /></td><td>{e.pid ?? "—"}</td></tr>
                  )} empty="No security events recorded yet." />
                </Panel>
                <Panel title="Security Audit" subtitle="Configuration findings" action={<button className="text-button" onClick={() => setPage("audits")}>View all →</button>}>
                  <div className="compact-list">
                    {audits.slice(0, 5).map((a) => <div className="compact-item" key={a.audit_id}><div><strong>{a.check_type}</strong><small>{a.description}</small></div><Badge value={a.severity} /></div>)}
                    {!audits.length && <div className="empty-state">Run an audit to collect findings.</div>}
                  </div>
                </Panel>
              </div>

              <Panel title="Top Processes by Memory" subtitle="Highest memory usage among returned processes" action={<button className="text-button" onClick={() => setPage("processes")}>View processes →</button>}>
                <Table columns={["PID", "Process", "User", "Status", "CPU", "Memory"]} rows={processes.slice().sort((a, b) => Number(b.memory_mb || 0) - Number(a.memory_mb || 0)).slice(0, 6).map((p) =>
                  <tr key={p.pid}><td>{p.pid}</td><td><strong>{p.name}</strong></td><td>{p.username}</td><td>{p.status}</td><td>{Number(p.cpu_percent || 0).toFixed(1)}%</td><td>{Number(p.memory_mb || 0).toFixed(2)} MB</td></tr>
                )} empty="No process data returned." />
              </Panel>
            </>
          )}

          {page === "processes" && <>
            <div className="page-heading"><div><div className="eyebrow">LIVE INVENTORY</div><h1>Process Monitor</h1><p>Inspect processes reported by Kali Linux.</p></div></div>
            <Panel title={`Processes (${filteredProcesses.length})`} subtitle="Search by PID, process, user, or status">
              <div className="table-tools"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search processes…" /></div>
              <Table columns={["PID", "Process", "User", "Status", "CPU", "Memory"]} rows={processRows} empty="No matching processes." />
            </Panel>
          </>}

          {page === "events" && <>
            <div className="page-heading"><div><div className="eyebrow">DETECTION ENGINE</div><h1>Security Events</h1><p>Review records created by the detection engine.</p></div></div>
            <Panel title={`Event history (${events.length})`}><Table columns={["ID", "Event", "Severity", "PID", "Recorded"]} rows={eventRows} empty="No security events recorded yet." /></Panel>
          </>}

          {page === "audits" && <>
            <div className="page-heading"><div><div className="eyebrow">CONFIGURATION REVIEW</div><h1>Security Audit</h1><p>Review read-only security configuration checks.</p></div>
              <button className="primary-button" disabled={busy} onClick={() => runAction(api.runAudit, (r) => `Audit finished. ${r.findings_collected ?? "Results"} findings collected.`)}>{busy ? "Running…" : "Run security audit"}</button>
            </div>
            <Panel title={`Audit results (${audits.length})`}><Table columns={["Check", "Status", "Severity", "Finding", "Checked"]} rows={auditRows} empty="Run an audit to collect findings." /></Panel>
          </>}

          {page === "incidents" && <>
            <div className="page-heading"><div><div className="eyebrow">INVESTIGATION WORKSPACE</div><h1>Incident Management</h1><p>Review incidents and update their investigation status.</p></div></div>
            <Panel title={`Incidents (${incidents.length})`}><Table columns={["ID", "Incident", "Severity", "Status", "Assign to", "Update status"]} rows={incidentRows} empty="No incidents recorded yet." /></Panel>
          </>}

          <footer className="page-footer"><span>RootShield Security Monitor</span><span>Refresh interval: 10 seconds · Updated: {dateText(updatedAt)}</span></footer>
        </div>

        <div className="quick-actions">
          <button className="secondary-button" onClick={refresh}>↻ Refresh</button>
          <button className="primary-button" disabled={busy} onClick={() => runAction(api.scanProcesses, (r) => `Scan complete. ${r.processes_scanned ?? "Process"} scanned; ${r.alerts_generated ?? "Alert"} alerts generated.`)}>{busy ? "Working…" : "Run process scan"}</button>
        </div>
      </main>
    </div>
  );
}
