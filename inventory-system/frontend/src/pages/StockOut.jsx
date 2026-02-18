import React, { useState } from 'react';
import BarcodeScanner from '../components/BarcodeScanner';
import { processSale } from '../services/api';

const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: 14 };
const thStyle = { textAlign: 'left', padding: '10px 12px', borderBottom: '2px solid #ddd', background: '#f8f9fa' };
const tdStyle = { padding: '8px 12px', borderBottom: '1px solid #eee' };

function StockOut() {
  const [cart, setCart] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const handleItemScanned = (item) => {
    setResult(null);
    setCart(prev => {
      const existing = prev.find(c => c.item_code === item.item_code);
      if (existing) {
        return prev.map(c =>
          c.item_code === item.item_code ? { ...c, qty: c.qty + 1 } : c
        );
      }
      return [...prev, {
        item_code: item.item_code,
        item_name: item.item_name,
        qty: 1,
        rate: item.standard_rate,
        stock_qty: item.stock_qty,
        barcode: item.barcode,
      }];
    });
  };

  const updateQty = (index, qty) => {
    if (qty <= 0) {
      setCart(prev => prev.filter((_, i) => i !== index));
    } else {
      setCart(prev => prev.map((item, i) => i === index ? { ...item, qty } : item));
    }
  };

  const removeItem = (index) => {
    setCart(prev => prev.filter((_, i) => i !== index));
  };

  const total = cart.reduce((sum, item) => sum + item.qty * item.rate, 0);

  const handleSale = async () => {
    setProcessing(true);
    setResult(null);
    try {
      const res = await processSale({
        items: cart.map(({ item_code, item_name, qty, rate }) => ({
          item_code, item_name, qty, rate,
        })),
        create_invoice: true,
      });
      setResult({ success: true, message: res.data.message });
      setCart([]);
    } catch (err) {
      setResult({ success: false, message: err.response?.data?.detail || err.message });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1e3a5f' }}>Stock Out - POS</h2>

      {/* Barcode Scanner */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <BarcodeScanner onItemScanned={handleItemScanned} />
      </div>

      {/* Cart */}
      <div style={{
        background: '#fff', borderRadius: 12, padding: 20, marginBottom: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <h3 style={{ marginBottom: 12 }}>Cart ({cart.length} items)</h3>
        {cart.length === 0 ? (
          <div style={{ color: '#888', padding: 16, textAlign: 'center' }}>
            Scan a barcode to add items
          </div>
        ) : (
          <>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Item</th>
                  <th style={thStyle}>Barcode</th>
                  <th style={thStyle}>In Stock</th>
                  <th style={thStyle}>Qty</th>
                  <th style={thStyle}>Rate</th>
                  <th style={thStyle}>Subtotal</th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {cart.map((item, i) => (
                  <tr key={item.item_code}>
                    <td style={tdStyle}>
                      <strong>{item.item_name}</strong>
                      <div style={{ fontSize: 12, color: '#888' }}>{item.item_code}</div>
                    </td>
                    <td style={tdStyle}>{item.barcode}</td>
                    <td style={tdStyle}>{item.stock_qty}</td>
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <button onClick={() => updateQty(i, item.qty - 1)}
                          style={{ width: 28, height: 28, border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', background: '#fff' }}>
                          -
                        </button>
                        <span style={{ minWidth: 32, textAlign: 'center', fontWeight: 600 }}>{item.qty}</span>
                        <button onClick={() => updateQty(i, item.qty + 1)}
                          style={{ width: 28, height: 28, border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', background: '#fff' }}>
                          +
                        </button>
                      </div>
                    </td>
                    <td style={tdStyle}>{item.rate.toFixed(2)}</td>
                    <td style={tdStyle}><strong>{(item.qty * item.rate).toFixed(2)}</strong></td>
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

            {/* Total & Checkout */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginTop: 20, paddingTop: 16, borderTop: '2px solid #eee',
            }}>
              <div style={{ fontSize: 24, fontWeight: 700 }}>
                Total: {total.toFixed(2)}
              </div>
              <button onClick={handleSale} disabled={processing}
                style={{
                  padding: '14px 40px', background: '#2e7d32', color: '#fff', border: 'none',
                  borderRadius: 8, fontSize: 18, cursor: 'pointer', fontWeight: 700,
                  opacity: processing ? 0.6 : 1,
                }}>
                {processing ? 'Processing...' : 'Complete Sale'}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Result */}
      {result && (
        <div style={{
          padding: 16, borderRadius: 8,
          background: result.success ? '#e8f5e9' : '#ffeaea',
          color: result.success ? '#2e7d32' : '#d32f2f',
        }}>
          {result.message}
        </div>
      )}
    </div>
  );
}

export default StockOut;
