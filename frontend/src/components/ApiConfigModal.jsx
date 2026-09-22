import React, { useState } from 'react';
import { X, Server, CheckCircle2, AlertCircle, RefreshCw, Globe } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl, checkBackendConnection } from '../api';

export default function ApiConfigModal({ isOpen, onClose, onConnected }) {
  const [apiUrl, setApiUrl] = useState(() => getApiBaseUrl());
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const prev = getApiBaseUrl();
      setApiBaseUrl(apiUrl);
      const res = await checkBackendConnection();
      setTestResult(res);
      if (!res.connected) {
        setApiBaseUrl(prev);
      }
    } catch (e) {
      setTestResult({ connected: false, error: e.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    setApiBaseUrl(apiUrl);
    if (onConnected) onConnected();
    onClose();
  };

  const handleReset = () => {
    const isLocal = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    const defaultUrl = isLocal ? 'http://localhost:8008' : (import.meta.env.VITE_API_URL || '');
    setApiUrl(defaultUrl);
    setApiBaseUrl(defaultUrl);
    setTestResult(null);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '520px',
        padding: '28px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        background: '#0f172a'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server size={22} color="#06b6d4" />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
                API Endpoint Configuration
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Cloudflare Pages Backend Connector
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Info Box */}
        <div style={{
          background: 'rgba(6, 182, 212, 0.08)',
          border: '1px solid rgba(6, 182, 212, 0.25)',
          borderRadius: '10px',
          padding: '12px 14px',
          marginBottom: '20px',
          fontSize: '12px',
          color: '#cbd5e1',
          lineHeight: 1.5
        }}>
          <div style={{ fontWeight: 600, color: '#38bdf8', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Globe size={14} /> Cloudflare Pages Deployment Note
          </div>
          If you deploy this frontend to Cloudflare Pages, set your remote FastAPI backend URL here (e.g. Render, Railway, Fly.io, or VPS). If left offline, the dashboard operates in <strong>Interactive Standby Demo Mode</strong>.
        </div>

        {/* Input */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Backend API Base URL
          </label>
          <input
            type="text"
            className="form-input"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="http://localhost:8008 or https://api.yourdomain.com"
            style={{ width: '100%', fontFamily: 'monospace', fontSize: '13px' }}
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setApiUrl('http://localhost:8008')}
              style={{
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                color: '#93c5fd',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11px',
                cursor: 'pointer'
              }}>
              Local (Port 8008)
            </button>
            <button
              type="button"
              onClick={() => setApiUrl('')}
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#6ee7b7',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11px',
                cursor: 'pointer'
              }}>
              Vite Proxy (/api)
            </button>
          </div>
        </div>

        {/* Test Result Message */}
        {testResult && (
          <div style={{
            marginBottom: '18px',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: testResult.connected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${testResult.connected ? '#22c55e' : '#ef4444'}`,
            color: testResult.connected ? '#86efac' : '#fca5a5'
          }}>
            {testResult.connected ? (
              <>
                <CheckCircle2 size={16} color="#22c55e" />
                <span>Connected! Backend v{testResult.data?.version || '2.1'} is online.</span>
              </>
            ) : (
              <>
                <AlertCircle size={16} color="#ef4444" />
                <span>Could not reach backend at this URL. Running in Demo Standby mode.</span>
              </>
            )}
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
          <button
            type="button"
            onClick={handleReset}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              borderRadius: '8px',
              padding: '8px 14px',
              fontSize: '12px',
              cursor: 'pointer'
            }}>
            Reset Default
          </button>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={handleTest}
              disabled={testing}
              style={{
                background: 'rgba(51, 65, 85, 0.6)',
                border: '1px solid var(--border-color)',
                color: 'white',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
              {testing ? <RefreshCw size={14} className="spin" /> : <RefreshCw size={14} />}
              Test Connection
            </button>

            <button
              type="button"
              onClick={handleSave}
              className="btn btn-primary"
              style={{ padding: '8px 18px', fontSize: '12px' }}>
              Save & Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
