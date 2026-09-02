import React, { useState, useEffect } from 'react';
import { Radio, Save, Send, CheckCircle, AlertTriangle, Key, ExternalLink } from 'lucide-react';
import { fetchIntegrationSettings, updateIntegrationSettings, testSocConnection } from '../api';

export default function IntegrationSettingsView() {
  const [settings, setSettings] = useState(null);
  const [targetName, setTargetName] = useState('');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isEnabled, setIsEnabled] = useState(true);
  const [alertOnGuilt, setAlertOnGuilt] = useState(true);
  const [alertOnCanary, setAlertOnCanary] = useState(true);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await fetchIntegrationSettings();
      setSettings(data);
      setTargetName(data.target_name || 'DecodeX Threat Hunting Platform');
      setEndpointUrl(data.endpoint_url || 'http://localhost:8001/api/v1/alerts');
      setApiKey(data.api_key || '');
      setIsEnabled(data.is_enabled ?? true);
      setAlertOnGuilt(data.alert_on_guilt ?? true);
      setAlertOnCanary(data.alert_on_canary ?? true);
    } catch (e) {
      console.error('Failed to load integration settings:', e);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg(null);
    try {
      const updated = await updateIntegrationSettings({
        target_name: targetName,
        endpoint_url: endpointUrl,
        api_key: apiKey,
        is_enabled: isEnabled,
        alert_on_guilt: alertOnGuilt,
        alert_on_canary: alertOnCanary
      });
      setSettings(updated);
      setSuccessMsg('✅ Integration settings saved successfully.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (e) {
      alert('Failed to save settings: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestPing = async () => {
    setTestLoading(true);
    setTestResult(null);
    try {
      const res = await testSocConnection();
      setTestResult(res);
    } catch (e) {
      setTestResult({ success: false, message: e.message });
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={20} color="#38bdf8" />
          <h2 style={{ fontSize: '20px', fontWeight: 800 }}>DecodeX Threat Hunting SOC Integration</h2>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Configure outbound security alert delivery to <strong>DecodeX Threat Hunting Platform</strong> (<code>github.com/Decoder420/DecodeX-Threat-Hunting-Platform</code>).
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px' }}>
        {/* Settings Form */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            {successMsg && (
              <div style={{ padding: '10px 14px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', borderRadius: '8px', color: '#34d399', fontSize: '13px' }}>
                {successMsg}
              </div>
            )}

            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Target SOC System Name</label>
              <input
                className="form-input"
                type="text"
                value={targetName}
                onChange={e => setTargetName(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                DecodeX Alert Ingestion Endpoint URL
              </label>
              <input
                className="form-input font-mono"
                type="text"
                placeholder="http://localhost:8001/api/v1/alerts"
                value={endpointUrl}
                onChange={e => setEndpointUrl(e.target.value)}
                required
              />
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                The endpoint where DLD will POST transformed security alerts with retry-backoff.
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Bearer Token / API Key (Optional)
              </label>
              <input
                className="form-input font-mono"
                type="password"
                placeholder="dld_soc_bearer_token..."
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '20px', padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={isEnabled}
                  onChange={e => setIsEnabled(e.target.checked)}
                  style={{ accentColor: 'var(--primary)' }}
                />
                <span>Enable Outbound Forwarding</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={alertOnCanary}
                  onChange={e => setAlertOnCanary(e.target.checked)}
                  style={{ accentColor: '#ef4444' }}
                />
                <span>Alert on Canary Traps</span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button type="submit" className="btn-primary" disabled={loading} style={{ flex: 1, justifyContent: 'center' }}>
                <Save size={15} /> {loading ? 'Saving...' : 'Save Configuration'}
              </button>
              
              <button
                type="button"
                className="btn-secondary"
                onClick={handleTestPing}
                disabled={testLoading}
                style={{ justifyContent: 'center' }}>
                <Send size={15} color="#38bdf8" /> {testLoading ? 'Testing...' : '⚡ Test Connection'}
              </button>
            </div>
          </form>
        </div>

        {/* Integration Status & Payload Preview */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', height: 'fit-content' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Connection Status</h3>
          
          {testResult ? (
            <div>
              <div style={{
                padding: '12px',
                borderRadius: '8px',
                background: testResult.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                border: testResult.success ? '1px solid #10b981' : '1px solid #ef4444',
                color: testResult.success ? '#34d399' : '#f87171',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '14px'
              }}>
                {testResult.success ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                {testResult.message}
              </div>

              {testResult.details && (
                <pre className="font-mono" style={{
                  background: '#090d16',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  overflowX: 'auto'
                }}>
                  {typeof testResult.details === 'object' ? JSON.stringify(testResult.details, null, 2) : testResult.details}
                </pre>
              )}
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Click <strong>⚡ Test Connection</strong> to dispatch a synthetic test probe through <code>alert_adapter.py</code> to verify connectivity with DecodeX Threat Hunting SOC.
            </div>
          )}

          <div style={{ borderTop: '1px solid var(--border-color)', marginTop: '20px', paddingTop: '16px', fontSize: '12px', color: 'var(--text-dim)' }}>
            <strong>Adapter Module:</strong> <code>backend/app/services/alert_adapter.py</code><br/>
            Supports zero-downtime schema adaptation when DecodeX's endpoint contract is finalized.
          </div>
        </div>
      </div>
    </div>
  );
}
