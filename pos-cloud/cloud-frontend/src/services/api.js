import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: `${API_BASE}/api`, timeout: 120000 });
const storeId = () => localStorage.getItem('store_id') || '';

export const getOverview    = ()             => api.get('/dashboard/overview',      { params: { store_id: storeId() } });
export const getSalesTrend  = (period)       => api.get('/dashboard/sales-trend',   { params: { store_id: storeId(), period } });
export const getTopItems    = (period, limit=5) => api.get('/dashboard/top-items',  { params: { store_id: storeId(), period, limit } });
export const getCashFlow    = (period)       => api.get('/dashboard/cash-flow',     { params: { store_id: storeId(), period } });
export const getLowStock    = ()             => api.get('/dashboard/low-stock',     { params: { store_id: storeId() } });
export const getOverdueUdhar= ()             => api.get('/dashboard/overdue-udhar', { params: { store_id: storeId() } });
export const getSyncLog     = (limit=5)      => api.get('/dashboard/sync-log',      { params: { store_id: storeId(), limit } });

export const queryInsight   = (question)     => api.post('/insight/query',  { question, store_id: storeId() });
export const getInsightCards= (period)       => api.get('/insight/cards',   { params: { store_id: storeId(), period } });

export const getUdhar       = (params)       => api.get('/udhar/',          { params: { store_id: storeId(), ...params } });
export const createUdhar    = (data)         => api.post('/udhar/',   data, { params: { store_id: storeId() } });
export const updateUdhar    = (id, data)     => api.patch(`/udhar/${id}`, data, { params: { store_id: storeId() } });
export const deleteUdhar    = (id)           => api.delete(`/udhar/${id}`, { params: { store_id: storeId() } });

export const getFollowups   = (params)       => api.get('/followup/',       { params: { store_id: storeId(), ...params } });
export const createFollowup = (data)         => api.post('/followup/', data,{ params: { store_id: storeId() } });
export const updateFollowup = (id, data)     => api.patch(`/followup/${id}`, data, { params: { store_id: storeId() } });
export const deleteFollowup = (id)           => api.delete(`/followup/${id}`, { params: { store_id: storeId() } });

export default api;
