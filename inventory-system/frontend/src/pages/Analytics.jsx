import React, { useState } from 'react';
import Dashboard from '../components/Dashboard';
import { getDemandForecast } from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

function Analytics() {
  const [forecastItem, setForecastItem] = useState('');
  const [forecast, setForecast] = useState(null);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [forecastError, setForecastError] = useState('');

  const handleForecast = async () => {
    if (!forecastItem.trim()) return;
    setLoadingForecast(true);
    setForecastError('');
    setForecast(null);
    try {
      const res = await getDemandForecast(forecastItem.trim());
      setForecast(res.data);
    } catch (err) {
      setForecastError(err.response?.data?.detail || err.message || 'Forecast failed');
    } finally {
      setLoadingForecast(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Analytics Dashboard</h2>

      <Dashboard />

      {/* Demand Forecast Tool */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 20, marginTop: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <h3 style={{ marginBottom: 12 }}>Demand Forecast</h3>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <input
            type="text"
            value={forecastItem}
            onChange={(e) => setForecastItem(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleForecast()}
            placeholder="Enter item code..."
            style={{
              padding: '10px 14px', border: '1px solid #ddd', borderRadius: 6,
              fontSize: 14, flex: 1,
            }}
          />
          <button onClick={handleForecast} disabled={loadingForecast || !forecastItem.trim()}
            style={{
              padding: '10px 20px', background: '#1e3a5f', color: '#fff', border: 'none',
              borderRadius: 6, cursor: 'pointer', opacity: loadingForecast ? 0.6 : 1,
            }}>
            {loadingForecast ? 'Loading...' : 'Forecast'}
          </button>
        </div>

        {forecastError && (
          <div style={{ color: '#d32f2f', padding: 8, background: '#ffeaea', borderRadius: 6, marginBottom: 12 }}>
            {forecastError}
          </div>
        )}

        {forecast && (
          <div>
            <div style={{ marginBottom: 12, fontSize: 14, color: '#666' }}>
              Average weekly demand: <strong>{forecast.avg_weekly_demand}</strong> units
            </div>
            {forecast.historical.length > 0 && (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={[
                  ...forecast.historical.map(h => ({ name: h.week, demand: h.demand, type: 'actual' })),
                  ...forecast.forecast.map(f => ({ name: `F${f.period}`, demand: f.predicted_demand, type: 'forecast' })),
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={11} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="demand" stroke="#1e3a5f" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
            {forecast.historical.length === 0 && (
              <div style={{ color: '#888', padding: 16 }}>No historical data for this item</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Analytics;
