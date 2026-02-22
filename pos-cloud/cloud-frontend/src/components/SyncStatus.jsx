import React, { useState, useEffect } from 'react';
import { getSyncLog } from '../services/api';
function SyncStatus() {
  const [info, setInfo] = useState(null);
  useEffect(() => { getSyncLog(1).then(r => setInfo((r.data.data || [])[0])).catch(() => {}); }, []);
  const color = !info ? '#ccc' : info.status === 'success' ? '#27ae60' : info.status === 'failed' ? '#e74c3c' : '#f39c12';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0f2f5', borderRadius: 20, padding: '4px 12px', fontSize: 12, color: '#555' }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
      {info ? `Last sync: ${new Date(info.sync_ended_at || info.sync_started_at).toLocaleString('en-IN')}` : 'No sync yet'}
    </span>
  );
}
export default SyncStatus;
