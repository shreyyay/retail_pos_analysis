import React, { useState, useRef } from 'react';
import { uploadInvoice } from '../services/api';

const dropZoneStyle = {
  border: '2px dashed #b0c4de',
  borderRadius: 12,
  padding: 48,
  textAlign: 'center',
  cursor: 'pointer',
  background: '#f8fafc',
  transition: 'border-color 0.2s',
};

const dropZoneActiveStyle = {
  ...dropZoneStyle,
  borderColor: '#1e3a5f',
  background: '#e8f0fe',
};

function InvoiceUpload({ onExtracted }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInput = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const res = await uploadInvoice(file);
      if (res.data.success) {
        onExtracted(res.data.data);
      } else {
        setError(res.data.message || 'Extraction failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  return (
    <div>
      <div
        style={dragging ? dropZoneActiveStyle : dropZoneStyle}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInput.current?.click()}
      >
        <input
          ref={fileInput}
          type="file"
          accept="image/*,application/pdf"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {loading ? (
          <div>
            <div style={{ fontSize: 24, marginBottom: 8 }}>Processing...</div>
            <div style={{ color: '#666' }}>Extracting invoice data with OCR + AI</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 36, marginBottom: 8 }}>+</div>
            <div style={{ fontSize: 16, fontWeight: 500 }}>
              Drop supplier invoice here or click to upload
            </div>
            <div style={{ color: '#888', marginTop: 8, fontSize: 13 }}>
              Supports JPEG, PNG, WebP, PDF
            </div>
          </div>
        )}
      </div>
      {error && (
        <div style={{ color: '#d32f2f', marginTop: 12, padding: 12, background: '#ffeaea', borderRadius: 8 }}>
          {error}
        </div>
      )}
    </div>
  );
}

export default InvoiceUpload;
