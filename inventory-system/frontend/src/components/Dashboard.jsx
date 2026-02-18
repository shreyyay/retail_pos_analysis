import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  getDashboardSummary, getReorderAlerts, getDeadStock, getSalesVelocity,
} from '../services/api';

const cardStyle = {
  background: '#fff',
  borderRadius: 12,
  padding: 20,
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  flex: 1,
  minWidth: 200,
};

const cardTitleStyle = { fontSize: 13, color: '#666', marginBottom: 4 };
const cardValueStyle = { fontSize: 28, fontWeight: 700, color: '#1e3a5f' };

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [deadStock, setDeadStock] = useState([]);
  const [velocity, setVelocity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [summaryRes, alertsRes, deadStockRes, velocityRes] = await Promise.all([
        getDashboardSummary(),
        getReorderAlerts(),
        getDeadStock(),
        getSalesVelocity(),
      ]);
      setSummary(summaryRes.data);
      setAlerts(alertsRes.data.alerts || []);
      setDeadStock(deadStockRes.data.items || []);
      setVelocity(velocityRes.data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#666' }}>Loading dashboard...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <div style={{ color: '#d32f2f', padding: 16, background: '#ffeaea', borderRadius: 8, marginBottom: 16 }}>
          {error}
        </div>
        <button onClick={loadData} style={{ padding: '8px 16px', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  const topVelocity = velocity.slice(0, 10);

  return (
    <div>
      {/* Summary Cards */}
      {summary && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          <div style={cardStyle}>
            <div style={cardTitleStyle}>Total Items</div>
            <div style={cardValueStyle}>{summary.total_items}</div>
          </div>
          <div style={cardStyle}>
            <div style={cardTitleStyle}>Stock Value</div>
            <div style={cardValueStyle}>{summary.total_stock_value.toLocaleString()}</div>
          </div>
          <div style={cardStyle}>
            <div style={cardTitleStyle}>Low Stock</div>
            <div style={{ ...cardValueStyle, color: '#f57c00' }}>{summary.low_stock_count}</div>
          </div>
          <div style={cardStyle}>
            <div style={cardTitleStyle}>Out of Stock</div>
            <div style={{ ...cardValueStyle, color: '#d32f2f' }}>{summary.out_of_stock_count}</div>
          </div>
        </div>
      )}

      {/* Sales Velocity Chart */}
      {topVelocity.length > 0 && (
        <div style={{ ...cardStyle, marginBottom: 24 }}>
          <h3 style={{ marginBottom: 16 }}>Top 10 Sales Velocity (30 days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topVelocity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="item_code" angle={-30} textAnchor="end" height={80} fontSize={11} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total_sold" fill="#1e3a5f" name="Total Sold" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Reorder Alerts */}
        <div style={cardStyle}>
          <h3 style={{ marginBottom: 12, color: '#f57c00' }}>
            Reorder Alerts ({alerts.length})
          </h3>
          {alerts.length === 0 ? (
            <div style={{ color: '#888', padding: 16 }}>No reorder alerts</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #eee' }}>
                  <th style={{ textAlign: 'left', padding: 8 }}>Item</th>
                  <th style={{ textAlign: 'right', padding: 8 }}>Stock</th>
                  <th style={{ textAlign: 'right', padding: 8 }}>Reorder Level</th>
                  <th style={{ textAlign: 'right', padding: 8 }}>Deficit</th>
                </tr>
              </thead>
              <tbody>
                {alerts.slice(0, 10).map((a, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: 8 }}>{a.item_name || a.item_code}</td>
                    <td style={{ textAlign: 'right', padding: 8 }}>{a.current_qty}</td>
                    <td style={{ textAlign: 'right', padding: 8 }}>{a.reorder_level}</td>
                    <td style={{ textAlign: 'right', padding: 8, color: '#d32f2f' }}>{a.deficit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Dead Stock */}
        <div style={cardStyle}>
          <h3 style={{ marginBottom: 12, color: '#666' }}>
            Dead Stock - 90 Days ({deadStock.length})
          </h3>
          {deadStock.length === 0 ? (
            <div style={{ color: '#888', padding: 16 }}>No dead stock identified</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #eee' }}>
                  <th style={{ textAlign: 'left', padding: 8 }}>Item</th>
                  <th style={{ textAlign: 'right', padding: 8 }}>Qty</th>
                  <th style={{ textAlign: 'right', padding: 8 }}>Days Inactive</th>
                </tr>
              </thead>
              <tbody>
                {deadStock.slice(0, 10).map((item, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: 8 }}>{item.item_name || item.item_code}</td>
                    <td style={{ textAlign: 'right', padding: 8 }}>{item.current_qty}</td>
                    <td style={{ textAlign: 'right', padding: 8 }}>{item.days_inactive}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
