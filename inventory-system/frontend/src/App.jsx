import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import StockIn from './pages/StockIn';
import StockOut from './pages/StockOut';
import Analytics from './pages/Analytics';
import Sales from './pages/Sales';
import Udhar from './pages/Udhar';
import Followup from './pages/Followup';

const navStyle = {
  display: 'flex',
  background: '#1e3a5f',
  padding: '0 24px',
  alignItems: 'center',
  height: 56,
  gap: 8,
};

const logoStyle = {
  color: '#fff',
  fontWeight: 700,
  fontSize: 18,
  marginRight: 32,
  textDecoration: 'none',
};

const linkStyle = {
  color: '#b0c4de',
  textDecoration: 'none',
  padding: '8px 16px',
  borderRadius: 6,
  fontSize: 14,
  fontWeight: 500,
};

const activeLinkStyle = {
  ...linkStyle,
  background: 'rgba(255,255,255,0.15)',
  color: '#fff',
};

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <nav style={navStyle}>
          <span style={logoStyle}>Inventory System</span>
          <NavLink to="/" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle} end>
            Stock In
          </NavLink>
          <NavLink to="/stock-out" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
            Stock Out
          </NavLink>
          <NavLink to="/analytics" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
            Analytics
          </NavLink>
          <NavLink to="/sales" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
            Sales
          </NavLink>
          <NavLink to="/udhar" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
            Udhar
          </NavLink>
          <NavLink to="/followup" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
            Follow-up
          </NavLink>
        </nav>

        <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<StockIn />} />
            <Route path="/stock-out" element={<StockOut />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/sales" element={<Sales />} />
            <Route path="/udhar" element={<Udhar />} />
            <Route path="/followup" element={<Followup />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
