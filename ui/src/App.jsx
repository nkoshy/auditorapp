import { useState, useEffect, useCallback } from 'react'

const API_BASE = window.UIAPI_URL || 'https://uiapi.68.220.202.177.nip.io'

const styles = {
  app: {
    minHeight: '100vh',
    background: '#0f1117',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    height: '52px',
    background: '#13151f',
    borderBottom: '1px solid #2a2d3a',
    flexShrink: 0,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '24px' },
  logo: { fontSize: '16px', fontWeight: 700, color: '#fff', letterSpacing: '0.5px' },
  tabs: { display: 'flex', gap: '4px' },
  tab: {
    padding: '6px 14px',
    borderRadius: '6px',
    border: 'none',
    background: 'transparent',
    color: '#8892a4',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
    transition: 'all 0.15s',
  },
  tabActive: {
    background: '#1e2130',
    color: '#e2e8f0',
  },
  headerRight: { display: 'flex', alignItems: 'center', gap: '12px' },
  liveBadge: {
    display: 'flex', alignItems: 'center', gap: '6px',
    padding: '4px 10px', borderRadius: '20px',
    background: '#1a2a1a', border: '1px solid #2d4a2d',
    color: '#4ade80', fontSize: '12px', fontWeight: 600,
  },
  liveDot: {
    width: '6px', height: '6px', borderRadius: '50%',
    background: '#4ade80', animation: 'pulse 2s infinite',
  },
  refreshBtn: {
    padding: '6px 14px', borderRadius: '6px',
    border: '1px solid #2a2d3a', background: '#1e2130',
    color: '#8892a4', cursor: 'pointer', fontSize: '13px',
    transition: 'all 0.15s',
  },
  filterBar: {
    display: 'flex', alignItems: 'center', gap: '12px',
    padding: '14px 24px',
    background: '#13151f',
    borderBottom: '1px solid #2a2d3a',
  },
  filterLabel: { color: '#8892a4', fontSize: '13px' },
  filterInput: {
    padding: '7px 12px', borderRadius: '6px',
    border: '1px solid #2a2d3a', background: '#1e2130',
    color: '#e2e8f0', fontSize: '13px', outline: 'none',
    minWidth: '200px',
    transition: 'border-color 0.15s',
  },
  limitSelect: {
    padding: '7px 10px', borderRadius: '6px',
    border: '1px solid #2a2d3a', background: '#1e2130',
    color: '#e2e8f0', fontSize: '13px', outline: 'none',
    cursor: 'pointer',
  },
  fetchBtn: {
    padding: '7px 18px', borderRadius: '6px',
    border: 'none', background: '#3b82f6',
    color: '#fff', cursor: 'pointer', fontSize: '13px',
    fontWeight: 600, transition: 'background 0.15s',
  },
  statsRow: {
    display: 'flex', gap: '16px',
    padding: '16px 24px',
    background: '#0f1117',
  },
  statCard: {
    flex: 1, padding: '16px 20px',
    background: '#13151f',
    borderRadius: '8px',
    border: '1px solid #2a2d3a',
  },
  statLabel: { color: '#8892a4', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' },
  statValue: { fontSize: '28px', fontWeight: 700, color: '#fff' },
  statSub: { fontSize: '11px', color: '#6b7280', marginTop: '4px' },
  main: { flex: 1, padding: '0 24px 24px', overflow: 'hidden' },
  tableWrapper: {
    background: '#13151f',
    borderRadius: '8px',
    border: '1px solid #2a2d3a',
    overflow: 'hidden',
    marginTop: '0',
  },
  table: { width: '100%', borderCollapse: 'collapse' },
  thead: { background: '#1a1d2a' },
  th: {
    padding: '10px 14px', textAlign: 'left',
    color: '#8892a4', fontSize: '11px', fontWeight: 600,
    textTransform: 'uppercase', letterSpacing: '0.5px',
    borderBottom: '1px solid #2a2d3a',
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '10px 14px',
    borderBottom: '1px solid #1e2130',
    fontSize: '12px',
    color: '#c8cdd6',
    fontFamily: 'monospace',
  },
  trEven: { background: '#13151f' },
  trOdd: { background: '#111420' },
  statusBadge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 700,
    minWidth: '36px',
    textAlign: 'center',
  },
  methodBadge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 700,
    minWidth: '40px',
    textAlign: 'center',
  },
  empty: {
    textAlign: 'center', padding: '48px',
    color: '#4b5563', fontSize: '14px',
  },
  loading: {
    textAlign: 'center', padding: '48px',
    color: '#6b7280', fontSize: '14px',
  },
}

function statusStyle(code) {
  if (code >= 200 && code < 300) return { background: '#14532d', color: '#4ade80' }
  if (code >= 400 && code < 500) return { background: '#7c2d12', color: '#fb923c' }
  if (code >= 500) return { background: '#450a0a', color: '#f87171' }
  return { background: '#1e2130', color: '#8892a4' }
}

function methodStyle(method) {
  const m = (method || '').toUpperCase()
  if (m === 'GET') return { background: '#1e3a5f', color: '#60a5fa' }
  if (m === 'POST') return { background: '#14532d', color: '#4ade80' }
  if (m === 'DELETE') return { background: '#450a0a', color: '#f87171' }
  if (m === 'PUT') return { background: '#451a03', color: '#fb923c' }
  return { background: '#1e2130', color: '#8892a4' }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [username, setUsername] = useState('')
  const [limit, setLimit] = useState(50)
  const [rows, setRows] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ limit })
      if (username) params.set('username', username)

      const [telRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/telemetry?${params}`),
        fetch(`${API_BASE}/api/stats${username ? `?username=${encodeURIComponent(username)}` : ''}`),
      ])

      if (!telRes.ok) throw new Error(`Telemetry API error: ${telRes.status}`)
      if (!statsRes.ok) throw new Error(`Stats API error: ${statsRes.status}`)

      const [tel, st] = await Promise.all([telRes.json(), statsRes.json()])
      setRows(tel)
      setStats(st)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [username, limit])

  useEffect(() => { fetchData() }, [])

  return (
    <div style={styles.app} data-testid="app">
      {/* Header */}
      <header style={styles.header} data-testid="header">
        <div style={styles.headerLeft}>
          <span style={styles.logo}>Telemetry</span>
          <nav style={styles.tabs} data-testid="nav-tabs">
            {['overview', 'log', 'metrics'].map(tab => (
              <button
                key={tab}
                style={tab === activeTab ? { ...styles.tab, ...styles.tabActive } : styles.tab}
                onClick={() => setActiveTab(tab)}
                data-testid={`tab-${tab}`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.liveBadge} data-testid="live-badge">
            <div style={styles.liveDot} />
            Live
          </div>
          <button style={styles.refreshBtn} onClick={fetchData} data-testid="refresh-btn">
            Refresh
          </button>
        </div>
      </header>

      {/* Filter Bar */}
      <div style={styles.filterBar} data-testid="filter-bar">
        <span style={styles.filterLabel}>User</span>
        <input
          style={styles.filterInput}
          type="text"
          placeholder="Filter by username..."
          value={username}
          onChange={e => setUsername(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && fetchData()}
          data-testid="username-filter"
        />
        <span style={styles.filterLabel}>Rows</span>
        <select
          style={styles.limitSelect}
          value={limit}
          onChange={e => setLimit(Number(e.target.value))}
          data-testid="limit-select"
        >
          {[25, 50, 100, 200].map(n => (
            <option key={n} value={n}>{n} rows</option>
          ))}
        </select>
        <button style={styles.fetchBtn} onClick={fetchData} data-testid="fetch-btn">
          Fetch
        </button>
      </div>

      {/* Stats Row */}
      <div style={styles.statsRow} data-testid="stats-row">
        <div style={styles.statCard} data-testid="stat-total">
          <div style={styles.statLabel}>Total Requests</div>
          <div style={styles.statValue}>{stats?.total ?? '—'}</div>
        </div>
        <div style={styles.statCard} data-testid="stat-duration">
          <div style={styles.statLabel}>Avg Duration</div>
          <div style={styles.statValue}>{stats ? `${stats.avg_duration_ms}ms` : '—'}</div>
        </div>
        <div style={styles.statCard} data-testid="stat-2xx">
          <div style={styles.statLabel}>2XX Success</div>
          <div style={{ ...styles.statValue, color: '#4ade80' }}>{stats?.success_2xx ?? '—'}</div>
        </div>
        <div style={styles.statCard} data-testid="stat-4xx">
          <div style={styles.statLabel}>4XX Client Errors</div>
          <div style={{ ...styles.statValue, color: '#fb923c' }}>{stats?.errors_4xx ?? '—'}</div>
        </div>
        <div style={styles.statCard} data-testid="stat-5xx">
          <div style={styles.statLabel}>5XX Server Errors</div>
          <div style={{ ...styles.statValue, color: '#f87171' }}>{stats?.errors_5xx ?? '—'}</div>
        </div>
      </div>

      {/* Table */}
      <main style={styles.main}>
        <div style={styles.tableWrapper}>
          {error && (
            <div style={{ padding: '16px 24px', color: '#f87171', fontSize: '13px' }}>
              Error: {error}
            </div>
          )}
          {loading ? (
            <div style={styles.loading}>Loading...</div>
          ) : (
            <table style={styles.table} data-testid="telemetry-table">
              <thead style={styles.thead}>
                <tr>
                  <th style={styles.th} data-testid="col-timestamp">Timestamp</th>
                  <th style={styles.th} data-testid="col-method">Method</th>
                  <th style={styles.th} data-testid="col-endpoint">Endpoint</th>
                  <th style={styles.th} data-testid="col-status">Status</th>
                  <th style={styles.th} data-testid="col-duration">Duration</th>
                  <th style={styles.th} data-testid="col-query">Query</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={styles.empty}>No telemetry data found</td>
                  </tr>
                ) : rows.map((row, i) => (
                  <tr
                    key={i}
                    style={i % 2 === 0 ? styles.trEven : styles.trOdd}
                    data-testid="telemetry-row"
                  >
                    <td style={styles.td} data-testid="cell-timestamp">
                      {row.event_time ? row.event_time.slice(0, 19).replace('T', ' ') : '—'}
                    </td>
                    <td style={styles.td} data-testid="cell-method">
                      <span style={{ ...styles.methodBadge, ...methodStyle(row.method) }}>
                        {row.method || '—'}
                      </span>
                    </td>
                    <td style={styles.td} data-testid="cell-endpoint">{row.endpoint || '—'}</td>
                    <td style={styles.td} data-testid="cell-status">
                      <span style={{ ...styles.statusBadge, ...statusStyle(row.status_code) }}>
                        {row.status_code || '—'}
                      </span>
                    </td>
                    <td style={styles.td} data-testid="cell-duration">
                      {row.duration_ms != null ? `${row.duration_ms.toFixed(1)}ms` : '—'}
                    </td>
                    <td style={styles.td} data-testid="cell-query">
                      {row.query_text || ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        button:hover { opacity: 0.85; }
        input:focus { border-color: #3b82f6 !important; }
      `}</style>
    </div>
  )
}
