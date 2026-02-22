import React, { useState, useEffect } from 'react';
import { getFollowups, createFollowup, updateFollowup, deleteFollowup } from '../services/api';

const card = { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 };
const btn = { padding: '8px 18px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500 };
const inp = { padding: '9px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, width: '100%', boxSizing: 'border-box' };
const EMPTY = { customer_name: '', phone: '', salesperson: '', notes: '', followup_date: new Date().toISOString().slice(0,10), next_followup_date: '', status: 'Open' };

function Followup() {
  const [records, setRecords] = useState([]); const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false); const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [sf, setSf] = useState('all'); const [cs, setCs] = useState(''); const [sp, setSp] = useState(''); const [fd, setFd] = useState(''); const [td, setTd] = useState('');

  const set = f => e => setForm({ ...form, [f]: e.target.value });

  const fetch_ = async (a=sf,b=cs,c=sp,d=fd,e=td) => {
    setLoading(true); setError('');
    try { const r = await getFollowups({ status: a, customer_name: b, salesperson: c, from_date: d, to_date: e }); setRecords(r.data.records); setCount(r.data.count); }
    catch (e) { setError(e.response?.data?.detail || e.message || 'Failed to load'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch_(); }, []);

  const handleSubmit = async e => {
    e.preventDefault(); setSubmitting(true); setError('');
    try { await createFollowup({ ...form, next_followup_date: form.next_followup_date || null }); setForm(EMPTY); setShowForm(false); fetch_(); }
    catch (e) { setError(e.response?.data?.detail || e.message || 'Failed to save'); }
    finally { setSubmitting(false); }
  };

  const openCount = records.filter(r => r.status === 'Open').length;

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Sales Follow-up</h2>
      <div style={card}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {['all','Open','Closed'].map(s => (
            <button key={s} onClick={() => { setSf(s); fetch_(s,cs,sp,fd,td); }}
              style={{ ...btn, background: sf===s ? '#1e3a5f' : '#f0f2f5', color: sf===s ? '#fff' : '#333' }}>
              {s === 'all' ? 'All' : s}
            </button>
          ))}
          <input type="text" placeholder="Customer..." value={cs} onChange={e => setCs(e.target.value)} onKeyDown={e => e.key==='Enter' && fetch_(sf,e.target.value,sp,fd,td)} style={{ ...inp, width: 150 }} />
          <input type="text" placeholder="Salesperson..." value={sp} onChange={e => setSp(e.target.value)} onKeyDown={e => e.key==='Enter' && fetch_(sf,cs,e.target.value,fd,td)} style={{ ...inp, width: 150 }} />
          <input type="date" value={fd} onChange={e => setFd(e.target.value)} style={{ ...inp, width: 140 }} />
          <span style={{ color: '#666' }}>to</span>
          <input type="date" value={td} onChange={e => setTd(e.target.value)} style={{ ...inp, width: 140 }} />
          <button onClick={() => fetch_(sf,cs,sp,fd,td)} style={{ ...btn, background: '#1e3a5f', color: '#fff' }}>Search</button>
          <button onClick={() => setShowForm(!showForm)} style={{ ...btn, background: '#27ae60', color: '#fff', marginLeft: 'auto' }}>{showForm ? 'Cancel' : '+ Add Follow-up'}</button>
        </div>
      </div>

      {showForm && (
        <div style={card}>
          <h3 style={{ marginBottom: 16, color: '#1e3a5f' }}>New Follow-up</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Customer Name *</label><input value={form.customer_name} onChange={set('customer_name')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Phone *</label><input value={form.phone} onChange={set('phone')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Salesperson *</label><input value={form.salesperson} onChange={set('salesperson')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Status</label><select value={form.status} onChange={set('status')} style={inp}><option>Open</option><option>Closed</option></select></div>
              <div style={{ gridColumn: '1/-1' }}><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Notes *</label><textarea value={form.notes} onChange={set('notes')} required rows={2} style={{ ...inp, resize: 'vertical' }} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Follow-up Date *</label><input type="date" value={form.followup_date} onChange={set('followup_date')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Next Follow-up Date</label><input type="date" value={form.next_followup_date} onChange={set('next_followup_date')} style={inp} /></div>
            </div>
            <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
              <button type="submit" disabled={submitting} style={{ ...btn, background: '#1e3a5f', color: '#fff', opacity: submitting ? 0.6 : 1 }}>{submitting ? 'Saving...' : 'Save'}</button>
              <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY); }} style={{ ...btn, background: '#f0f2f5', color: '#333' }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}><div style={{ fontSize: 26, fontWeight: 700, color: '#1e3a5f' }}>{count}</div><div style={{ color: '#666', marginTop: 4 }}>Total Entries</div></div>
        <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}><div style={{ fontSize: 26, fontWeight: 700, color: openCount > 0 ? '#e67e22' : '#27ae60' }}>{openCount}</div><div style={{ color: '#666', marginTop: 4 }}>Open Follow-ups</div></div>
      </div>

      {error && <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b', padding: 14 }}>{error}</div>}
      {loading && <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>Loading...</div>}
      {!loading && records.length > 0 && (
        <div style={card}><div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead><tr style={{ background: '#f0f2f5' }}>{['Customer','Phone','Salesperson','Notes','Date','Next Date','Status','Actions'].map(h => <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#1e3a5f', whiteSpace: 'nowrap' }}>{h}</th>)}</tr></thead>
            <tbody>{records.map((r,i) => (
              <tr key={r.id} style={{ borderBottom: '1px solid #f0f2f5', background: i%2===0 ? '#fff' : '#fafafa' }}>
                <td style={{ padding: '10px 14px', fontWeight: 500 }}>{r.customer_name}</td>
                <td style={{ padding: '10px 14px' }}>{r.phone}</td>
                <td style={{ padding: '10px 14px' }}>{r.salesperson}</td>
                <td style={{ padding: '10px 14px', maxWidth: 200, wordBreak: 'break-word', fontSize: 13, color: '#555' }}>{r.notes}</td>
                <td style={{ padding: '10px 14px' }}>{r.followup_date}</td>
                <td style={{ padding: '10px 14px', color: '#888' }}>{r.next_followup_date || '—'}</td>
                <td style={{ padding: '10px 14px' }}><span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: r.status==='Closed' ? '#e8f5e9' : '#fff3e0', color: r.status==='Closed' ? '#2e7d32' : '#e65100' }}>{r.status}</span></td>
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                  {r.status==='Open' && <button onClick={() => updateFollowup(r.id, { status: 'Closed' }).then(() => fetch_())} style={{ ...btn, padding: '4px 10px', background: '#2980b9', color: '#fff', marginRight: 6, fontSize: 12 }}>Close</button>}
                  <button onClick={() => { if(window.confirm('Delete?')) deleteFollowup(r.id).then(() => fetch_()); }} style={{ ...btn, padding: '4px 10px', background: '#e74c3c', color: '#fff', fontSize: 12 }}>Delete</button>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div></div>
      )}
      {!loading && records.length===0 && !error && <div style={{ ...card, textAlign: 'center', color: '#666', padding: 40 }}>No follow-up entries found.</div>}
    </div>
  );
}
export default Followup;
