import React, { useState, useEffect } from 'react';
import { getUdhar, createUdhar, updateUdhar, deleteUdhar } from '../services/api';

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

const inputStyle = {
  padding: '9px 12px',
  border: '1px solid #ddd',
  borderRadius: 6,
  fontSize: 14,
  width: '100%',
  boxSizing: 'border-box',
};

const EMPTY_FORM = {
  customer_name: '',
  phone: '',
  items: '',
  amount: '',
  date_given: new Date().toISOString().slice(0, 10),
  due_date: '',
  status: 'Pending',
};

function Udhar() {
  const [records, setRecords] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [customerSearch, setCustomerSearch] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const fetchRecords = async (sf = statusFilter, cs = customerSearch, fd = fromDate, td = toDate) => {
    setLoading(true);
    setError('');
    try {
      const params = { status: sf, customer_name: cs, from_date: fd, to_date: td };
      const res = await getUdhar(params);
      setRecords(res.data.records);
      setCount(res.data.count);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load Udhar entries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRecords(); }, []);

  const handleFormChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await createUdhar({ ...form, amount: parseFloat(form.amount) });
      setForm(EMPTY_FORM);
      setShowForm(false);
      fetchRecords();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to save entry');
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkPaid = async (id) => {
    try {
      await updateUdhar(id, { status: 'Paid' });
      fetchRecords();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this Udhar entry?')) return;
    try {
      await deleteUdhar(id);
      fetchRecords();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete entry');
    }
  };

  const pendingTotal = records
    .filter((r) => r.status === 'Pending')
    .reduce((sum, r) => sum + Number(r.amount), 0);

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Udhar (Credit Sales)</h2>

      {/* Filters */}
      <div style={card}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {['all', 'Pending', 'Paid'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); fetchRecords(s, customerSearch, fromDate, toDate); }}
              style={{
                ...btnBase,
                background: statusFilter === s ? '#1e3a5f' : '#f0f2f5',
                color: statusFilter === s ? '#fff' : '#333',
              }}
            >
              {s === 'all' ? 'All' : s}
            </button>
          ))}
          <input
            type="text"
            placeholder="Search customer..."
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchRecords(statusFilter, e.target.value, fromDate, toDate)}
            style={{ ...inputStyle, width: 180 }}
          />
          <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)}
            style={{ ...inputStyle, width: 150 }} />
          <span style={{ color: '#666' }}>to</span>
          <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)}
            style={{ ...inputStyle, width: 150 }} />
          <button
            onClick={() => fetchRecords(statusFilter, customerSearch, fromDate, toDate)}
            style={{ ...btnBase, background: '#1e3a5f', color: '#fff' }}
          >
            Search
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            style={{ ...btnBase, background: '#27ae60', color: '#fff', marginLeft: 'auto' }}
          >
            {showForm ? 'Cancel' : '+ Add Udhar'}
          </button>
        </div>
      </div>

      {/* Add form */}
      {showForm && (
        <div style={card}>
          <h3 style={{ marginBottom: 16, color: '#1e3a5f' }}>New Udhar Entry</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Customer Name *</label>
                <input name="customer_name" value={form.customer_name} onChange={handleFormChange} required style={inputStyle} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Phone *</label>
                <input name="phone" value={form.phone} onChange={handleFormChange} required style={inputStyle} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Items Given *</label>
                <textarea name="items" value={form.items} onChange={handleFormChange} required rows={2}
                  placeholder="e.g. Rice 5kg, Sugar 2kg, Oil 1L"
                  style={{ ...inputStyle, resize: 'vertical' }} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Amount (₹) *</label>
                <input name="amount" type="number" min="0" step="0.01" value={form.amount} onChange={handleFormChange} required style={inputStyle} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Status</label>
                <select name="status" value={form.status} onChange={handleFormChange} style={inputStyle}>
                  <option>Pending</option>
                  <option>Paid</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Date Given *</label>
                <input name="date_given" type="date" value={form.date_given} onChange={handleFormChange} required style={inputStyle} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#555', display: 'block', marginBottom: 4 }}>Due Date *</label>
                <input name="due_date" type="date" value={form.due_date} onChange={handleFormChange} required style={inputStyle} />
              </div>
            </div>
            <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
              <button type="submit" disabled={submitting}
                style={{ ...btnBase, background: '#1e3a5f', color: '#fff', opacity: submitting ? 0.6 : 1 }}>
                {submitting ? 'Saving...' : 'Save Entry'}
              </button>
              <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY_FORM); }}
                style={{ ...btnBase, background: '#f0f2f5', color: '#333' }}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Summary */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: '#1e3a5f' }}>{count}</div>
          <div style={{ color: '#666', marginTop: 4 }}>Total Entries</div>
        </div>
        <div style={{ ...card, marginBottom: 0, flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: '#c0392b' }}>
            ₹{pendingTotal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
          <div style={{ color: '#666', marginTop: 4 }}>Pending Amount</div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ ...card, background: '#fff5f5', color: '#c0392b', borderLeft: '4px solid #c0392b', padding: 14 }}>
          {error}
        </div>
      )}

      {loading && <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>Loading...</div>}

      {/* Table */}
      {!loading && records.length > 0 && (
        <div style={card}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#f0f2f5' }}>
                  {['Customer', 'Phone', 'Items', 'Amount (₹)', 'Date Given', 'Due Date', 'Status', 'Actions'].map((h) => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#1e3a5f', whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((r, i) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #f0f2f5', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '10px 14px', fontWeight: 500 }}>{r.customer_name}</td>
                    <td style={{ padding: '10px 14px' }}>{r.phone}</td>
                    <td style={{ padding: '10px 14px', maxWidth: 200, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{r.items}</td>
                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      ₹{Number(r.amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '10px 14px' }}>{r.date_given}</td>
                    <td style={{ padding: '10px 14px' }}>{r.due_date}</td>
                    <td style={{ padding: '10px 14px' }}>
                      <span style={{
                        padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600,
                        background: r.status === 'Paid' ? '#e8f5e9' : '#fff3e0',
                        color: r.status === 'Paid' ? '#2e7d32' : '#e65100',
                      }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                      {r.status === 'Pending' && (
                        <button onClick={() => handleMarkPaid(r.id)}
                          style={{ ...btnBase, padding: '4px 10px', background: '#27ae60', color: '#fff', marginRight: 6, fontSize: 12 }}>
                          Mark Paid
                        </button>
                      )}
                      <button onClick={() => handleDelete(r.id)}
                        style={{ ...btnBase, padding: '4px 10px', background: '#e74c3c', color: '#fff', fontSize: 12 }}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && records.length === 0 && !error && (
        <div style={{ ...card, textAlign: 'center', color: '#666', padding: 40 }}>
          No Udhar entries found.
        </div>
      )}
    </div>
  );
}

export default Udhar;
