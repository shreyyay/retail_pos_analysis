import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Overview from './pages/Overview';
import SalesTrends from './pages/SalesTrends';
import AiInsights from './pages/AiInsights';
import Udhar from './pages/Udhar';
import Followup from './pages/Followup';

const nav = { display: 'flex', background: '#1e3a5f', padding: '0 24px', alignItems: 'center', height: 56, gap: 8 };
const lk = { color: '#b0c4de', textDecoration: 'none', padding: '8px 16px', borderRadius: 6, fontSize: 14, fontWeight: 500 };
const al = { ...lk, background: 'rgba(255,255,255,0.15)', color: '#fff' };

function StoreSelector({ onSave }) {
  const [val, setVal] = useState(localStorage.getItem('store_id') || '');
  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: 16, padding: 40, boxShadow: '0 4px 24px rgba(0,0,0,0.1)', width: 360 }}>
        <h2 style={{ color: '#1e3a5f', marginTop: 0, marginBottom: 8 }}>Retail POS Cloud</h2>
        <p style={{ color: '#888', marginBottom: 24, fontSize: 14 }}>Enter your Store ID to continue</p>
        <input type="text" value={val} onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && val.trim() && onSave(val.trim())}
          placeholder="e.g. STORE001"
          style={{ width: '100%', padding: '12px 14px', border: '1px solid #ddd', borderRadius: 8, fontSize: 15, boxSizing: 'border-box', marginBottom: 16 }} />
        <button onClick={() => val.trim() && onSave(val.trim())}
          style={{ width: '100%', padding: 12, background: '#1e3a5f', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, cursor: 'pointer', fontWeight: 600 }}>
          Enter Dashboard
        </button>
      </div>
    </div>
  );
}

function App() {
  const [storeId, setStoreId] = useState(localStorage.getItem('store_id') || '');
  const save = id => { localStorage.setItem('store_id', id); setStoreId(id); };

  if (!storeId) return <StoreSelector onSave={save} />;

  return (
    <Router>
      <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <nav style={nav}>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: 18, marginRight: 32 }}>POS Cloud</span>
          <NavLink to="/"        style={({ isActive }) => isActive ? al : lk} end>Overview</NavLink>
          <NavLink to="/trends"  style={({ isActive }) => isActive ? al : lk}>Sales Trends</NavLink>
          <NavLink to="/insights"style={({ isActive }) => isActive ? al : lk}>AI Insights</NavLink>
          <NavLink to="/udhar"   style={({ isActive }) => isActive ? al : lk}>Udhar</NavLink>
          <NavLink to="/followup"style={({ isActive }) => isActive ? al : lk}>Follow-up</NavLink>
          <button onClick={() => { localStorage.removeItem('store_id'); setStoreId(''); }}
            style={{ marginLeft: 'auto', background: 'rgba(255,255,255,0.1)', border: 'none', color: '#b0c4de', padding: '6px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
            {storeId} ×
          </button>
        </nav>
        <div style={{ padding: 24, maxWidth: 1280, margin: '0 auto' }}>
          <Routes>
            <Route path="/"         element={<Overview />} />
            <Route path="/trends"   element={<SalesTrends />} />
            <Route path="/insights" element={<AiInsights />} />
            <Route path="/udhar"    element={<Udhar />} />
            <Route path="/followup" element={<Followup />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
export default App;
