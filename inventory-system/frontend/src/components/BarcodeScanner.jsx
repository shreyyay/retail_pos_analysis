import React, { useState, useRef, useEffect } from 'react';
import { lookupBarcode } from '../services/api';

const inputStyle = {
  padding: '12px 16px',
  fontSize: 18,
  border: '2px solid #d0d5dd',
  borderRadius: 8,
  width: '100%',
  outline: 'none',
};

function BarcodeScanner({ onItemScanned }) {
  const [barcode, setBarcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleScan = async (code) => {
    if (!code.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await lookupBarcode(code.trim());
      if (res.data.success) {
        onItemScanned(res.data);
        setBarcode('');
      } else {
        setError(`Item not found for barcode: ${code}`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Lookup failed');
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleScan(barcode);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          ref={inputRef}
          type="text"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Scan or enter barcode..."
          style={inputStyle}
          disabled={loading}
        />
        <button
          onClick={() => handleScan(barcode)}
          disabled={loading || !barcode.trim()}
          style={{
            padding: '12px 24px',
            background: '#1e3a5f',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 16,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Looking up...' : 'Look Up'}
        </button>
      </div>
      {error && (
        <div style={{ color: '#d32f2f', marginTop: 8, padding: 8, background: '#ffeaea', borderRadius: 6, fontSize: 14 }}>
          {error}
        </div>
      )}
      <div style={{ marginTop: 8, color: '#888', fontSize: 13 }}>
        Use a barcode scanner or type the barcode manually. Press Enter to look up.
      </div>
    </div>
  );
}

export default BarcodeScanner;
