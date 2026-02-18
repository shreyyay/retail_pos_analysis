import React, { useState, useEffect } from 'react';
import { searchSales } from '../services/api';

const card = {
  background: '#fff',
  borderRadius: 12,
  padding: 20,
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  marginBottom: 24,
};

const btnBase = {
  padding: '8px 18px',
  borderRadius: 6,
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 500,
};

const PERIODS = [
  { label: 'Today', value: 'today' },
  { label: 'Last 7 Days', value: '7d' },
  { label: 'Last 30 Days', value: '30d' },
  { label: 'Custom', value: 'custom' },
];

function Sales() {
  const [period, setPeriod] = useState('7d');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const fetchSales = async (p = period, fd = fromDate, td = toDate) => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const params = { period: p, limit: 200 };
      if (p === 'custom') {
        params.from_date = fd;
        params.to_date = td;
      }
      const res = await searchSales(params);
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to load sales';
      if (err.response?.status === 503) {
        setError('ERPNext is offline. Please check your connection.');
      } else {
        setError(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales('7d', '', '');
  }, []);

  const handlePeriodChange = (p) => {
    setPeriod(p);
    if (p !== 'custom') fetchSales(p, '', '');
  };

  const totalAmount = result?.invoices?.reduce((sum, inv) => sum + (inv.grand_total || 0), 0) || 0;

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Sales</h2>

      {/* Filter bar */}
      <div style={card}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => handlePeriodChange(p.value)}
              style={{
                ...btnBase,
                background: period === p.value ? '#1e3a5f' : '#f0f2f5',
                color: period === p.value ? '#fff' : '#333',
              }}
            >
              {p.label}
            </button>
          ))}

          {period === 'custom' && (
            <>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14 }}
              />
              <span style={{ color: '#666' }}>to</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14 }}
              />
              <button
                onClick={() => fetchSales('custom', fromDate, toDate)}
                disabled={!fromDate || !toDate || loading}
                style={{
                  ...btnBase,
                  background: '#1e3a5f',
                  color: '#fff',
                  opacity: (!fromDate || !toDate || loading) ? 0.5 : 1,
                }}
              >
                Search
              </button>
            </>
          )}
        </div>
      </div>

      {/* Summary */}
      {result && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#1e3a5f' }}>{result.count}</div>
            <div style={{ color: '#666', marginTop: 4 }}>Invoices</div>
          </div>
          <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#1e3a5f' }}>
              ₹{totalAmount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </div>
            <div style={{ color: '#666', marginTop: 4 }}>Total Sales</div>
          </div>
          <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>Period</div>
            <div style={{ fontWeight: 600, color: '#333', marginTop: 2 }}>
              {result.from_date} → {result.to_date}
            </div>
          </div>
        </div>
      )}

      {/* Loading / Error */}
      {loading && <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>Loading...</div>}
      {error && (
        <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b' }}>
          {error}
        </div>
      )}

      {/* Table */}
      {result && result.invoices.length > 0 && (
        <div style={card}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f0f2f5' }}>
                  {['Date', 'Invoice #', 'Customer', 'Amount (₹)', 'Status'].map((h) => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#1e3a5f' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.invoices.map((inv, i) => (
                  <tr key={inv.name} style={{ borderBottom: '1px solid #f0f2f5', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '10px 14px' }}>{inv.posting_date}</td>
                    <td style={{ padding: '10px 14px', fontWeight: 500 }}>{inv.name}</td>
                    <td style={{ padding: '10px 14px' }}>{inv.customer}</td>
                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      ₹{Number(inv.grand_total).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span style={{
                        padding: '2px 10px',
                        borderRadius: 12,
                        fontSize: 12,
                        fontWeight: 600,
                        background: inv.status === 'Paid' ? '#e8f5e9' : '#fff3e0',
                        color: inv.status === 'Paid' ? '#2e7d32' : '#e65100',
                      }}>
                        {inv.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result && result.invoices.length === 0 && (
        <div style={{ ...card, textAlign: 'center', color: '#666', padding: 40 }}>
          No sales found for this period.
        </div>
      )}
    </div>
  );
}

export default Sales;
