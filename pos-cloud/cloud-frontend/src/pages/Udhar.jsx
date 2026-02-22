import React, { useState, useEffect } from 'react';
import { getUdhar, createUdhar, updateUdhar, deleteUdhar } from '../services/api';

const card = { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: 24 };
const btn = { padding: '8px 18px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500 };
const inp = { padding: '9px 12px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, width: '100%', boxSizing: 'border-box' };
const EMPTY = { customer_name: '', phone: '', items: '', amount: '', date_given: new Date().toISOString().slice(0,10), due_date: '', status: 'Pending' };

function Udhar() {
  const [records, setRecords] = useState([]); const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false); const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [sf, setSf] = useState('all'); const [cs, setCs] = useState(''); const [fd, setFd] = useState(''); const [td, setTd] = useState('');

  const set = f => e => setForm({ ...form, [f]: e.target.value });

  const fetch_ = async (a=sf, b=cs, c=fd, d=td) => {
    setLoading(true); setError('');
    try { const r = await getUdhar({ status: a, customer_name: b, from_date: c, to_date: d }); setRecords(r.data.records); setCount(r.data.count); }
    catch (e) { setError(e.response?.data?.detail || e.message || 'Failed to load'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch_(); }, []);

  const handleSubmit = async e => {
    e.preventDefault(); setSubmitting(true); setError('');
    try { await createUdhar({ ...form, amount: parseFloat(form.amount) }); setForm(EMPTY); setShowForm(false); fetch_(); }
    catch (e) { setError(e.response?.data?.detail || e.message || 'Failed to save'); }
    finally { setSubmitting(false); }
  };

  const pending = records.filter(r => r.status === 'Pending').reduce((s, r) => s + Number(r.amount), 0);

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Udhar (Credit Sales)</h2>
      <div style={card}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {['all','Pending','Paid'].map(s => (
            <button key={s} onClick={() => { setSf(s); fetch_(s,cs,fd,td); }}
              style={{ ...btn, background: sf===s ? '#1e3a5f' : '#f0f2f5', color: sf===s ? '#fff' : '#333' }}>
              {s === 'all' ? 'All' : s}
            </button>
          ))}
          <input type="text" placeholder="Search customer..." value={cs} onChange={e => setCs(e.target.value)}
            onKeyDown={e => e.key==='Enter' && fetch_(sf,e.target.value,fd,td)} style={{ ...inp, width: 180 }} />
          <input type="date" value={fd} onChange={e => setFd(e.target.value)} style={{ ...inp, width: 150 }} />
          <span style={{ color: '#666' }}>to</span>
          <input type="date" value={td} onChange={e => setTd(e.target.value)} style={{ ...inp, width: 150 }} />
          <button onClick={() => fetch_(sf,cs,fd,td)} style={{ ...btn, background: '#1e3a5f', color: '#fff' }}>Search</button>
          <button onClick={() => setShowForm(!showForm)} style={{ ...btn, background: '#27ae60', color: '#fff', marginLeft: 'auto' }}>
            {showForm ? 'Cancel' : '+ Add Udhar'}
          </button>
        </div>
      </div>

      {showForm && (
        <div style={card}>
          <h3 style={{ marginBottom: 16, color: '#1e3a5f' }}>New Udhar Entry</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[['customer_name','Customer Name *','text',true],['phone','Phone *','text',true]].map(([f,l,t,r]) => (
                <div key={f}><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>{l}</label>
                  <input type={t} value={form[f]} onChange={set(f)} required={r} style={inp} /></div>
              ))}
              <div style={{ gridColumn: '1/-1' }}><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Items Given *</label>
                <textarea value={form.items} onChange={set('items')} required rows={2} placeholder="e.g. Rice 5kg, Sugar 2kg" style={{ ...inp, resize: 'vertical' }} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Amount (₹) *</label>
                <input type="number" min="0" step="0.01" value={form.amount} onChange={set('amount')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Status</label>
                <select value={form.status} onChange={set('status')} style={inp}><option>Pending</option><option>Paid</option></select></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Date Given *</label>
                <input type="date" value={form.date_given} onChange={set('date_given')} required style={inp} /></div>
              <div><label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Due Date *</label>
                <input type="date" value={form.due_date} onChange={set('due_date')} required style={inp} /></div>
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
        <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}><div style={{ fontSize: 26, fontWeight: 700, color: '#c0392b' }}>₹{pending.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div><div style={{ color: '#666', marginTop: 4 }}>Pending Amount</div></div>
      </div>

      {error && <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b', padding: 14 }}>{error}</div>}
      {loading && <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>Loading...</div>}
      {!loading && records.length > 0 && (
        <div style={card}><div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead><tr style={{ background: '#f0f2f5' }}>{['Customer','Phone','Items','Amount (₹)','Date Given','Due Date','Status','Actions'].map(h => <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#1e3a5f', whiteSpace: 'nowrap' }}>{h}</th>)}</tr></thead>
            <tbody>{records.map((r, i) => (
              <tr key={r.id} style={{ borderBottom: '1px solid #f0f2f5', background: i%2===0 ? '#fff' : '#fafafa' }}>
                <td style={{ padding: '10px 14px', fontWeight: 500 }}>{r.customer_name}</td>
                <td style={{ padding: '10px 14px' }}>{r.phone}</td>
                <td style={{ padding: '10px 14px', maxWidth: 180, wordBreak: 'break-word', fontSize: 13 }}>{r.items}</td>
                <td style={{ padding: '10px 14px', fontWeight: 600 }}>₹{Number(r.amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                <td style={{ padding: '10px 14px' }}>{r.date_given}</td>
                <td style={{ padding: '10px 14px' }}>{r.due_date}</td>
                <td style={{ padding: '10px 14px' }}><span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: r.status==='Paid' ? '#e8f5e9' : '#fff3e0', color: r.status==='Paid' ? '#2e7d32' : '#e65100' }}>{r.status}</span></td>
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                  {r.status==='Pending' && <button onClick={() => updateUdhar(r.id, { status: 'Paid' }).then(() => fetch_())} style={{ ...btn, padding: '4px 10px', background: '#27ae60', color: '#fff', marginRight: 6, fontSize: 12 }}>Mark Paid</button>}
                  <button onClick={() => { if(window.confirm('Delete?')) deleteUdhar(r.id).then(() => fetch_()); }} style={{ ...btn, padding: '4px 10px', background: '#e74c3c', color: '#fff', fontSize: 12 }}>Delete</button>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div></div>
      )}
      {!loading && records.length===0 && !error && <div style={{ ...card, textAlign: 'center', color: '#666', padding: 40 }}>No Udhar entries found.</div>}
    </div>
  );
}
export default Udhar;
