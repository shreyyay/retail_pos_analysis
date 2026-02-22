import React, { useState, useEffect } from 'react';
import { getInsightCards } from '../services/api';
import ChatBox from '../components/ChatBox';

const PERIODS = ['daily', 'weekly', 'monthly', 'quarterly', 'half-yearly', 'annually'];
const card = { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' };
const btn = (active) => ({ padding: '6px 16px', borderRadius: 20, border: active ? 'none' : '1px solid #ddd', background: active ? '#1e3a5f' : '#fff', color: active ? '#fff' : '#555', cursor: 'pointer', fontSize: 13 });

const CARD_META = {
  sales_summary: { label: 'Sales Summary', color: '#2980b9' },
  top_items:     { label: 'Top Items',      color: '#27ae60' },
  least_items:   { label: 'Least Selling',  color: '#e67e22' },
  cash_flow:     { label: 'Cash Flow',      color: '#8e44ad' },
  overdue_udhar: { label: 'Overdue Udhar',  color: '#c0392b' },
  low_stock:     { label: 'Low Stock',      color: '#e74c3c' },
};

function AiInsights() {
  const [period, setPeriod] = useState('weekly');
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async (p) => {
    setLoading(true); setError(''); setCards([]);
    try { const r = await getInsightCards(p); setCards(r.data.cards || []); }
    catch (e) { setError(e.response?.data?.detail || e.message || 'Failed to load insights'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(period); }, [period]);

  const display = loading ? Object.keys(CARD_META).map(t => ({ type: t, answer: '' })) : cards;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <h2 style={{ color: '#1e3a5f', margin: 0 }}>AI Insights</h2>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {PERIODS.map(p => <button key={p} onClick={() => setPeriod(p)} disabled={loading} style={btn(period === p)}>{p.charAt(0).toUpperCase() + p.slice(1)}</button>)}
        </div>
        {loading && <span style={{ color: '#888', fontSize: 13 }}>Generating insights…</span>}
      </div>
      {error && <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b', marginBottom: 24 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20, marginBottom: 32 }}>
        {display.map((c, i) => {
          const meta = CARD_META[c.type] || { label: c.type, color: '#1e3a5f' };
          return (
            <div key={i} style={{ ...card, borderTop: `4px solid ${meta.color}` }}>
              <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#888', marginBottom: 8, fontWeight: 600 }}>{meta.label}</div>
              {loading
                ? <div style={{ height: 60, background: '#f0f2f5', borderRadius: 8 }} />
                : <div style={{ fontSize: 14, color: '#333', lineHeight: 1.6 }}>{c.answer || 'No data available'}</div>}
            </div>
          );
        })}
      </div>

      <div style={card}>
        <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 16, fontSize: 15 }}>Ask Your Store Data</h3>
        <ChatBox />
      </div>
    </div>
  );
}
export default AiInsights;
