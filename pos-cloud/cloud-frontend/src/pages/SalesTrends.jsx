import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getSalesTrend, getTopItems, getCashFlow } from '../services/api';

const card = { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 };
const PERIODS = ['daily', 'weekly', 'monthly', 'quarterly', 'half-yearly', 'annually'];
const btn = (active) => ({ padding: '6px 16px', borderRadius: 20, border: active ? 'none' : '1px solid #ddd', background: active ? '#1e3a5f' : '#fff', color: active ? '#fff' : '#555', cursor: 'pointer', fontSize: 13, fontWeight: active ? 600 : 400 });
const fmt = (n) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });

function SalesTrends() {
  const [period, setPeriod] = useState('weekly');
  const [trend, setTrend] = useState([]);
  const [top, setTop] = useState([]);
  const [least, setLeast] = useState([]);
  const [cashFlow, setCashFlow] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async (p) => {
    setLoading(true);
    try {
      const [tRes, iRes, cRes] = await Promise.all([getSalesTrend(p), getTopItems(p, 5), getCashFlow(p)]);
      setTrend(tRes.data.data || []); setTop(iRes.data.top || []); setLeast(iRes.data.least || []); setCashFlow(cRes.data.data || []);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  useEffect(() => { load(period); }, [period]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <h2 style={{ color: '#1e3a5f', margin: 0 }}>Sales Trends</h2>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {PERIODS.map(p => <button key={p} onClick={() => setPeriod(p)} style={btn(period === p)}>{p.charAt(0).toUpperCase() + p.slice(1)}</button>)}
        </div>
      </div>
      {loading && <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>Loading…</div>}
      {!loading && <>
        <div style={card}>
          <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 16, fontSize: 15 }}>Daily Sales — {period}</h3>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f5" />
                <XAxis dataKey="sale_date" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={v => [`₹${fmt(v)}`, 'Sales']} />
                <Line type="monotone" dataKey="total_sales" stroke="#1e3a5f" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>No data for this period</div>}
        </div>

        <div style={card}>
          <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 16, fontSize: 15 }}>Net Cash Flow — {period}</h3>
          {cashFlow.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cashFlow}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f5" />
                <XAxis dataKey="flow_date" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={v => [`₹${fmt(v)}`, '']} />
                <Legend />
                <Bar dataKey="total_in" name="Sales In" fill="#27ae60" radius={[3,3,0,0]} />
                <Bar dataKey="total_out" name="Purchases Out" fill="#e74c3c" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>No cash flow data</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div style={card}>
            <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 12, fontSize: 15 }}>Top 5 Items — {period}</h3>
            {top.length === 0 ? <div style={{ color: '#999' }}>No data</div> : top.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #f0f2f5', fontSize: 13 }}>
                <span><span style={{ color: '#1e3a5f', marginRight: 8, fontWeight: 700 }}>{i+1}.</span>{item.item_name}</span>
                <span style={{ color: '#27ae60', fontWeight: 600 }}>₹{fmt(item.revenue)}</span>
              </div>
            ))}
          </div>
          <div style={card}>
            <h3 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 12, fontSize: 15 }}>Least Selling — {period}</h3>
            {least.length === 0 ? <div style={{ color: '#999' }}>No data</div> : least.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #f0f2f5', fontSize: 13 }}>
                <span>{item.item_name}</span>
                <span style={{ color: '#e67e22', fontWeight: 600 }}>₹{fmt(item.revenue)}</span>
              </div>
            ))}
          </div>
        </div>
      </>}
    </div>
  );
}
export default SalesTrends;
