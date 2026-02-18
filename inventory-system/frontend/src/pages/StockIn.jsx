import React, { useState } from 'react';
import InvoiceUpload from '../components/InvoiceUpload';
import { confirmStockIn } from '../services/api';

const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: 14 };
const thStyle = { textAlign: 'left', padding: '10px 12px', borderBottom: '2px solid #ddd', background: '#f8f9fa' };
const tdStyle = { padding: '8px 12px', borderBottom: '1px solid #eee' };
const inputCellStyle = {
  padding: '4px 8px', border: '1px solid #ddd', borderRadius: 4, width: '100%',
  fontSize: 14,
};

function StockIn() {
  const [invoiceData, setInvoiceData] = useState(null);
  const [items, setItems] = useState([]);
  const [header, setHeader] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const handleExtracted = (data) => {
    setInvoiceData(data);
    setHeader(data.header);
    setItems(data.line_items.map((item, i) => ({ ...item, id: i })));
    setResult(null);
  };

  const updateItem = (index, field, value) => {
    setItems(prev => prev.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const removeItem = (index) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  const handleConfirm = async () => {
    setSubmitting(true);
    setResult(null);
    try {
      const res = await confirmStockIn({
        header,
        line_items: items,
      });
      setResult({ success: true, message: res.data.message, entry: res.data.entry_name });
    } catch (err) {
      setResult({ success: false, message: err.response?.data?.detail || err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setInvoiceData(null);
    setItems([]);
    setHeader(null);
    setResult(null);
  };

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Stock In - Invoice Processing</h2>

      {!invoiceData ? (
        <InvoiceUpload onExtracted={handleExtracted} />
      ) : (
        <div>
          {/* Invoice Header */}
          <div style={{
            background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20,
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}>
            <h3 style={{ marginBottom: 12 }}>Invoice Details</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <div>
                <label style={{ fontSize: 12, color: '#666' }}>Supplier</label>
                <div style={{ fontWeight: 600 }}>{header?.supplier_name || '-'}</div>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#666' }}>Invoice Number</label>
                <div style={{ fontWeight: 600 }}>{header?.invoice_number || '-'}</div>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#666' }}>Date</label>
                <div style={{ fontWeight: 600 }}>{header?.invoice_date || '-'}</div>
              </div>
            </div>
          </div>

          {/* Line Items Table */}
          <div style={{
            background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20,
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}>
            <h3 style={{ marginBottom: 12 }}>Line Items ({items.length})</h3>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Item Name</th>
                  <th style={thStyle}>Qty</th>
                  <th style={thStyle}>Unit</th>
                  <th style={thStyle}>Unit Price</th>
                  <th style={thStyle}>Total</th>
                  <th style={thStyle}>GST</th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => (
                  <tr key={i}>
                    <td style={tdStyle}>
                      <input style={inputCellStyle} value={item.item_name}
                        onChange={(e) => updateItem(i, 'item_name', e.target.value)} />
                    </td>
                    <td style={tdStyle}>
                      <input style={{ ...inputCellStyle, width: 80 }} type="number" value={item.quantity}
                        onChange={(e) => updateItem(i, 'quantity', parseFloat(e.target.value) || 0)} />
                    </td>
                    <td style={tdStyle}>
                      <input style={{ ...inputCellStyle, width: 60 }} value={item.unit}
                        onChange={(e) => updateItem(i, 'unit', e.target.value)} />
                    </td>
                    <td style={tdStyle}>
                      <input style={{ ...inputCellStyle, width: 100 }} type="number" step="0.01" value={item.unit_price}
                        onChange={(e) => updateItem(i, 'unit_price', parseFloat(e.target.value) || 0)} />
                    </td>
                    <td style={tdStyle}>
                      {(item.quantity * item.unit_price).toFixed(2)}
                    </td>
                    <td style={tdStyle}>{item.gst_rate}</td>
                    <td style={tdStyle}>
                      <button onClick={() => removeItem(i)}
                        style={{ color: '#d32f2f', border: 'none', background: 'none', cursor: 'pointer' }}>
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={handleConfirm} disabled={submitting || items.length === 0}
              style={{
                padding: '12px 32px', background: '#2e7d32', color: '#fff', border: 'none',
                borderRadius: 8, fontSize: 16, cursor: 'pointer', fontWeight: 600,
                opacity: submitting ? 0.6 : 1,
              }}>
              {submitting ? 'Creating Stock Entry...' : 'Confirm & Create Stock Entry'}
            </button>
            <button onClick={reset}
              style={{
                padding: '12px 24px', background: '#fff', color: '#333', border: '1px solid #ddd',
                borderRadius: 8, fontSize: 16, cursor: 'pointer',
              }}>
              Upload New Invoice
            </button>
          </div>

          {/* Result */}
          {result && (
            <div style={{
              marginTop: 16, padding: 16, borderRadius: 8,
              background: result.success ? '#e8f5e9' : '#ffeaea',
              color: result.success ? '#2e7d32' : '#d32f2f',
            }}>
              {result.message}
              {result.entry && <span> - Entry: <strong>{result.entry}</strong></span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StockIn;
