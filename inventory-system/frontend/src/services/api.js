import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 60000,
});

// Stock-In
export const uploadInvoice = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/stock-in/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const confirmStockIn = (data) =>
  api.post('/stock-in/confirm', data);

// Stock-Out
export const lookupBarcode = (barcode) =>
  api.get(`/stock-out/lookup/${barcode}`);

export const processSale = (data) =>
  api.post('/stock-out/sale', data);

// Dashboard
export const getDashboardSummary = () =>
  api.get('/dashboard/summary');

export const getReorderAlerts = () =>
  api.get('/dashboard/reorder-alerts');

export const getDeadStock = (days = 90) =>
  api.get(`/dashboard/dead-stock?days=${days}`);

export const getDemandForecast = (itemCode, periods = 4) =>
  api.get(`/dashboard/demand-forecast/${itemCode}?periods=${periods}`);

export const getSalesVelocity = (days = 30) =>
  api.get(`/dashboard/sales-velocity?days=${days}`);

// Sales Search
export const searchSales = (params) =>
  api.get('/sales/search', { params });

// Udhar (Credit Sales)
export const getUdhar = (params) =>
  api.get('/udhar/', { params });

export const createUdhar = (data) =>
  api.post('/udhar/', data);

export const updateUdhar = (id, data) =>
  api.patch(`/udhar/${id}`, data);

export const deleteUdhar = (id) =>
  api.delete(`/udhar/${id}`);

// Follow-up
export const getFollowups = (params) =>
  api.get('/followup/', { params });

export const createFollowup = (data) =>
  api.post('/followup/', data);

export const updateFollowup = (id, data) =>
  api.patch(`/followup/${id}`, data);

export const deleteFollowup = (id) =>
  api.delete(`/followup/${id}`);

export default api;
