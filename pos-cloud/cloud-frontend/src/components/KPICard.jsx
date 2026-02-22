import React from 'react';
function KPICard({ title, value, subtitle, color = '#1e3a5f', loading = false }) {
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '20px 24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderTop: `4px solid ${color}` }}>
      <div style={{ fontSize: 12, color: '#888', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</div>
      {loading
        ? <div style={{ height: 36, background: '#f0f2f5', borderRadius: 6 }} />
        : <div style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1.2 }}>{value}</div>}
      {subtitle && <div style={{ fontSize: 12, color: '#999', marginTop: 6 }}>{subtitle}</div>}
    </div>
  );
}
export default KPICard;
