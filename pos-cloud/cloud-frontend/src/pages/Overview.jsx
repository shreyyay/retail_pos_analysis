import React, { useState, useEffect } from 'react';
import { getOverview, getLowStock, getOverdueUdhar } from '../services/api';
import KPICard from '../components/KPICard';
import SyncStatus from '../components/SyncStatus';

const card = { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 };
const fmt = (n, d = 0) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: d });

function Overview() {
  const [overview, setOverview] = useState(null);
  const [lowStock, setLowStock] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getOverview(), getLowStock(), getOverdueUdhar()])
      .then(([ov, ls, od]) => { setOverview(ov.data); setLowStock(ls.data.data || []); setOverdue(od.data.data || []); })
      .catch(e => setError(e.response?.data?.detail || e.message || 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  const today = overview?.today_sales ?? 0;
  const yest  = overview?.yesterday_sales ?? 0;
  const pct   = yest > 0 ? `${today >= yest ? '+' : ''}${(((today - yest) / yest) * 100).toFixed(1)}% vs yesterday` : '';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ color: '#1e3a5f', margin: 0 }}>Store Overview</h2>
        <SyncStatus />
      </div>
      {error && <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b' }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <KPICard title="Today's Sales"    value={`₹${fmt(today)}`}                                    subtitle={pct}             color="#1e3a5f" loading={loading} />
        <KPICard title="Yesterday's Sales" value={`₹${fmt(yest)}`}                                    color="#2980b9"            loading={loading} />
        <KPICard title="Pending Udhar"    value={`₹${fmt(overview?.pending_udhar_amount)}`}            subtitle={`${overview?.pending_udhar_count ?? 0} entries`} color="#e67e22" loading={loading} />
        <KPICard title="Overdue Udhar"    value={overdue.length}                                       subtitle="past due date"   color={overdue.length > 0 ? '#c0392b' : '#27ae60'} loading={loading} />
        <KPICard title="Low Stock Items"  value={lowStock.length}                                      subtitle="need attention"  color={lowStock.length > 5 ? '#e74c3c' : '#f39c12'} loading={loading} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={card}>
          <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 14, fontSize: 15 }}>Low Stock Alert</h3>
          {loading ? <div style={{ color: '#999' }}>Loading…</div> : lowStock.length === 0
            ? <div style={{ color: '#27ae60' }}>All items well stocked</div>
            : <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead><tr style={{ background: '#f0f2f5' }}>
                  {['Item', 'Qty', 'Unit'].map(h => <th key={h} style={{ padding: '7px 10px', textAlign: 'left', color: '#555', fontWeight: 600 }}>{h}</th>)}
                </tr></thead>
                <tbody>{lowStock.slice(0, 8).map((item, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f2f5' }}>
                    <td style={{ padding: '7px 10px', fontWeight: 500 }}>{item.item_name}</td>
                    <td style={{ padding: '7px 10px', color: item.closing_qty === 0 ? '#e74c3c' : '#e67e22', fontWeight: 600 }}>{fmt(item.closing_qty, 2)}</td>
                    <td style={{ padding: '7px 10px', color: '#888' }}>{item.unit || '—'}</td>
                  </tr>
                ))}</tbody>
              </table>}
        </div>
        <div style={card}>
          <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 14, fontSize: 15 }}>Overdue Udhar</h3>
          {loading ? <div style={{ color: '#999' }}>Loading…</div> : overdue.length === 0
            ? <div style={{ color: '#27ae60' }}>No overdue Udhar</div>
            : <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead><tr style={{ background: '#f0f2f5' }}>
                  {['Customer', 'Amount', 'Days Overdue'].map(h => <th key={h} style={{ padding: '7px 10px', textAlign: 'left', color: '#555', fontWeight: 600 }}>{h}</th>)}
                </tr></thead>
                <tbody>{overdue.slice(0, 8).map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f2f5' }}>
                    <td style={{ padding: '7px 10px', fontWeight: 500 }}>{r.customer_name}</td>
                    <td style={{ padding: '7px 10px', fontWeight: 600, color: '#c0392b' }}>₹{fmt(r.amount)}</td>
                    <td style={{ padding: '7px 10px', color: '#e74c3c' }}>{r.days_overdue}d</td>
                  </tr>
                ))}</tbody>
              </table>}
        </div>
      </div>
    </div>
  );
}
export default Overview;
