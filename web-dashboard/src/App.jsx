import React, { useState, useEffect } from 'react';
import { fetchTrafficStats, fetchTrafficLogs, fetchSettings, updateSetting } from './api';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from 'recharts';
import { Activity, LayoutDashboard, Settings as SettingsIcon, Database, Terminal } from 'lucide-react';

// --- Dashboard Component ---
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrafficStats().then(data => {
      setStats(data.stats);
      setLoading(false);
    }).catch(console.error);

    // Auto-refresh every 10s
    const interval = setInterval(() => {
      fetchTrafficStats().then(data => setStats(data.stats)).catch(console.error);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-8 text-center">Loading dashboard...</div>;
  if (!stats) return <div className="p-8 text-center text-red-400">Failed to load stats. Check backend.</div>;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl mb-6">Overview</h2>

      {/* Key Metrics */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-value">{stats.total_requests.toLocaleString()}</div>
          <div className="stat-label">Total Requests</div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-value">{stats.daily_requests.length > 0 ? stats.daily_requests[stats.daily_requests.length - 1].count : 0}</div>
          <div className="stat-label">Requests Today</div>
        </div>
        <div className="glass-panel stat-card">
          {/* Sum costs from distribution */}
          <div className="stat-value">${stats.cost_distribution.reduce((acc, curr) => acc + (curr.total_cost || 0), 0).toFixed(4)}</div>
          <div className="stat-label">Total Estimated Cost</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>

        <div className="glass-panel p-6">
          <h3 className="mb-4 text-lg">Traffic History (Last 7 Days)</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.daily_requests}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} itemStyle={{ color: '#fff' }} />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-6">
          <h3 className="mb-4 text-lg">Provider Distribution</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.provider_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="count"
                  nameKey="provider"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {stats.provider_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} itemStyle={{ color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="glass-panel p-6 mb-6">
        <h3 className="mb-4 text-lg">Cost by Provider</h3>
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats.cost_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="provider" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} itemStyle={{ color: '#fff' }} />
              <Bar dataKey="total_cost" fill="#82ca9d" radius={[4, 4, 0, 0]}>
                {stats.cost_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// --- Logs Component ---
const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const LIMIT = 20;

  useEffect(() => {
    const loadLogs = () => {
      setLoading(true);
      fetchTrafficLogs(LIMIT, page * LIMIT).then(data => {
        setLogs(data.logs);
        setLoading(false);
      });
    };

    loadLogs();
    const interval = setInterval(loadLogs, 5000); // Poll logs
    return () => clearInterval(interval);
  }, [page]);

  return (
    <div className="animate-fade-in glass-panel p-6">
      <div className="flex justify-between items-center mb-4" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h2 className="text-xl">Traffic Logs</h2>
        <div>
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)} style={{ marginRight: '0.5rem', opacity: page === 0 ? 0.5 : 1 }}>Prev</button>
          <span style={{ margin: '0 1rem' }}>Page {page + 1}</span>
          <button onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Provider</th>
              <th>Model</th>
              <th>Latency (s)</th>
              <th>Tokens (In/Out)</th>
              <th>Cost ($)</th>
              <th>Prompt (Preview)</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td style={{ whiteSpace: 'nowrap', color: '#94a3b8' }}>{new Date(log.timestamp).toLocaleTimeString()}</td>
                <td><span style={{ padding: '2px 6px', borderRadius: '4px', backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', fontSize: '0.8rem' }}>{log.provider}</span></td>
                <td style={{ fontSize: '0.9rem' }}>{log.model}</td>
                <td>{log.latency ? log.latency.toFixed(2) : '-'}</td>
                <td>{log.tokens_in} / {log.tokens_out}</td>
                <td>{log.cost ? log.cost.toFixed(5) : '0.000'}</td>
                <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#cbd5e1' }} title={log.prompt}>
                  {log.prompt}
                </td>
              </tr>
            ))}
            {logs.length === 0 && !loading && (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>No logs found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Settings Component ---
const Settings = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updates, setUpdates] = useState({}); // Tracking changes

  useEffect(() => {
    fetchSettings().then(data => {
      setKeys(data.keys);
      setLoading(false);
    });
  }, []);

  const handleChange = (name, val) => {
    setUpdates(prev => ({ ...prev, [name]: val }));
  };

  const handleSave = async (name) => {
    if (!updates[name]) return;
    try {
      await updateSetting(name, updates[name]);
      alert(`Updated ${name} successfully! restart backend to apply.`);
      // Optimistic update or refresh
      setKeys(prev => prev.map(k => k.name === name ? { ...k, value: '****' } : k));
      setUpdates(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    } catch (err) {
      alert('Failed to update: ' + err.message);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  return (
    <div className="animate-fade-in glass-panel p-6" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 className="text-xl mb-6">API Configuration</h2>
      <div className="space-y-4" style={{ display: 'grid', gap: '1.5rem' }}>
        {keys.map(k => (
          <div key={k.name}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>{k.name}</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="password"
                placeholder={k.is_set ? "•••••••• (Set)" : "Not Set"}
                value={updates[k.name] !== undefined ? updates[k.name] : ""}
                onChange={(e) => handleChange(k.name, e.target.value)}
              />
              <button
                onClick={() => handleSave(k.name)}
                disabled={!updates[k.name]}
                style={{ opacity: !updates[k.name] ? 0.5 : 1 }}
              >
                Save
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// --- Main App ---
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="app">
      {/* Sidebar / Navigation */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, width: '250px',
        backgroundColor: 'var(--bg-secondary)', borderRight: '1px solid var(--border-color)',
        padding: '2rem 1rem', display: 'flex', flexDirection: 'column', gap: '1rem', zIndex: 100
      }}>
        <div style={{ marginBottom: '2rem', fontSize: '1.5rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff' }}>
          <Activity color="#3b82f6" /> ClawBrain
        </div>

        <button
          onClick={() => setActiveTab('dashboard')}
          style={{
            justifyContent: 'flex-start', display: 'flex', gap: '0.75rem',
            backgroundColor: activeTab === 'dashboard' ? 'var(--accent-color)' : 'transparent',
            textAlign: 'left'
          }}
        >
          <LayoutDashboard size={18} /> Dashboard
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          style={{
            justifyContent: 'flex-start', display: 'flex', gap: '0.75rem',
            backgroundColor: activeTab === 'logs' ? 'var(--accent-color)' : 'transparent',
            textAlign: 'left'
          }}
        >
          <Database size={18} /> Traffic Logs
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          style={{
            justifyContent: 'flex-start', display: 'flex', gap: '0.75rem',
            backgroundColor: activeTab === 'settings' ? 'var(--accent-color)' : 'transparent',
            textAlign: 'left'
          }}
        >
          <SettingsIcon size={18} /> Settings
        </button>
      </nav>

      {/* Main Content */}
      <main style={{ marginLeft: '250px', padding: '2rem' }}>
        <div className="container">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'logs' && <Logs />}
          {activeTab === 'settings' && <Settings />}
        </div>
      </main>
    </div>
  );
}

export default App;
