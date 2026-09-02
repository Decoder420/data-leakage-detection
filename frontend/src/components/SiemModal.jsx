import React, { useState } from 'react';
import { X, Send, Radio, CheckCircle } from 'lucide-react';
import { testSiemWebhook } from '../api';

export default function SiemModal({ isOpen, onClose, analysisId }) {
  if (!isOpen || !analysisId) return null;

  const [siemType, setSiemType] = useState('Splunk');
  const [loading, setLoading] = useState(false);
  const [responsePayload, setResponsePayload] = useState(null);

  const handleSend = async () => {
    setLoading(true);
    try {
      const res = await testSiemWebhook({
        analysis_id: analysisId,
        siem_type: siemType
      });
      setResponsePayload(res);
    } catch (e) {
      alert('Failed to dispatch alert payload');
    } finally {
      setLoading(false);
    }
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
        maxWidth: '560px',
        padding: '28px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        background: '#0f172a'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radio size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>SIEM & SOC Webhook Integration</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Simulate dispatching a structured JSON security alert payload to your enterprise SIEM or incident response channel.
        </p>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
          {['Splunk', 'Elastic SOC', 'Datadog', 'Slack'].map(type => (
            <button
              key={type}
              onClick={() => setSiemType(type)}
              style={{
                flex: 1,
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid',
                borderColor: siemType === type ? 'var(--primary)' : 'var(--border-color)',
                background: siemType === type ? 'rgba(14, 165, 233, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                color: siemType === type ? '#38bdf8' : 'var(--text-muted)',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}>
              {type}
            </button>
          ))}
        </div>

        <button className="btn-primary" onClick={handleSend} disabled={loading} style={{ width: '100%', justifyContent: 'center', marginBottom: '16px' }}>
          <Send size={15} /> {loading ? 'Dispatching...' : `Dispatch Alert Payload to ${siemType}`}
        </button>

        {responsePayload && (
          <div style={{ marginTop: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#34d399', fontWeight: 600, marginBottom: '6px' }}>
              <CheckCircle size={14} /> 200 OK • Payload Dispatched to SIEM Collector
            </div>
            <pre className="font-mono" style={{
              background: '#090d16',
              padding: '14px',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#38bdf8',
              overflowX: 'auto',
              maxHeight: '220px',
              border: '1px solid var(--border-color)'
            }}>
              {JSON.stringify(responsePayload, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
