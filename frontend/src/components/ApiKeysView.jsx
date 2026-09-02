import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, Copy, CheckCircle, ShieldCheck } from 'lucide-react';
import { fetchApiKeys, createApiKey, revokeApiKey } from '../api';

export default function ApiKeysView() {
  const [keys, setKeys] = useState([]);
  const [keyName, setKeyName] = useState('DecodeX SOC Service Account');
  const [newKeyCreated, setNewKeyCreated] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadKeys();
  }, []);

  const loadKeys = async () => {
    try {
      const data = await fetchApiKeys();
      setKeys(data);
    } catch (e) {
      console.error('Failed to load API keys:', e);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await createApiKey({ name: keyName });
      setNewKeyCreated(res);
      setKeyName('');
      loadKeys();
    } catch (e) {
      alert('Failed to create API key: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={20} color="var(--primary)" />
            <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Service Accounts & API Keys</h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Generate <code>X-API-Key</code> credentials for automated service-to-service calls from DecodeX Threat Hunting SOC.
          </p>
        </div>
      </div>

      {newKeyCreated && (
        <div className="glass-panel" style={{
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #10b981',
          background: 'rgba(16, 185, 129, 0.1)',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={16} /> API Key Generated Successfully
            </span>
            <span style={{ fontSize: '11px', color: '#fca5a5' }}>Copy now — this key will never be shown again!</span>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              readOnly
              value={newKeyCreated.raw_api_key}
              className="form-input font-mono"
              style={{ background: '#090d16', color: '#38bdf8', fontSize: '13px' }}
            />
            <button className="btn-primary" onClick={() => handleCopy(newKeyCreated.raw_api_key)}>
              <Copy size={14} /> {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
        {/* Create Form */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', height: 'fit-content' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Generate Service API Key</h3>
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Service / Integration Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. DecodeX SOC Collector Agent"
                value={keyName}
                onChange={e => setKeyName(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center' }}>
              <Plus size={15} /> {loading ? 'Generating...' : 'Generate API Key'}
            </button>
          </form>
        </div>

        {/* Keys Table */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Active Service Keys</h3>
          {keys.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-dim)' }}>
              No API keys generated yet.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Service Name</th>
                  <th>Key Prefix</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {keys.map(k => (
                  <tr key={k.id}>
                    <td style={{ fontWeight: 600 }}>{k.name}</td>
                    <td className="font-mono">{k.key_prefix}...</td>
                    <td><span className="badge badge-green">Active</span></td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ color: '#f87171', padding: '4px 10px', fontSize: '12px' }}
                        onClick={async () => {
                          if (confirm(`Revoke key for ${k.name}?`)) {
                            await revokeApiKey(k.id);
                            loadKeys();
                          }
                        }}>
                        <Trash2 size={13} /> Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
