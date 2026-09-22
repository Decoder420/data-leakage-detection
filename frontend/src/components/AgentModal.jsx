import React, { useState, useEffect } from 'react';
import { X, Users, Shield } from 'lucide-react';
import { createAgent, updateAgent } from '../api';

export default function AgentModal({ isOpen, onClose, agentToEdit, onSaved }) {
  const [name, setName] = useState('');
  const [org, setOrg] = useState('');
  const [email, setEmail] = useState('');
  const [risk, setRisk] = useState('Medium');
  const [trust, setTrust] = useState(85);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (agentToEdit) {
      setName(agentToEdit.name);
      setOrg(agentToEdit.organization);
      setEmail(agentToEdit.contact_email);
      setRisk(agentToEdit.risk_level);
      setTrust(agentToEdit.trust_score);
    } else {
      setName('');
      setOrg('');
      setEmail('');
      setRisk('Medium');
      setTrust(85);
    }
  }, [agentToEdit]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        name,
        organization: org || name,
        contact_email: email,
        risk_level: risk,
        trust_score: Number(trust)
      };
      let res;
      if (agentToEdit) {
        res = await updateAgent(agentToEdit.id, payload);
      } else {
        res = await createAgent(payload);
      }
      onSaved(res);
      onClose();
    } catch (err) {
      setError(err.message);
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
        maxWidth: '480px',
        padding: '28px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        background: '#0f172a'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={20} color="var(--primary)" />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>
              {agentToEdit ? 'Edit Third-Party Agent' : 'Register Third-Party Agent'}
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '8px', color: '#f87171', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Agent / Partner Name</label>
            <input className="form-input" type="text" placeholder="e.g. Acme Analytics Partner" value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Organization</label>
            <input className="form-input" type="text" placeholder="e.g. Acme Corp LLC" value={org} onChange={e => setOrg(e.target.value)} required />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Security Contact Email</label>
            <input className="form-input" type="email" placeholder="security@acme.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Risk Rating</label>
              <select className="form-select" value={risk} onChange={e => setRisk(e.target.value)}>
                <option value="Low">Low Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="High">High Risk</option>
                <option value="Critical">Critical Risk</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Trust Score ({trust}/100)</label>
              <input type="number" min="0" max="100" className="form-input" value={trust} onChange={e => setTrust(e.target.value)} />
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '12px' }}>
            {loading ? 'Saving...' : (agentToEdit ? 'Save Changes' : 'Register Vendor Agent')}
          </button>
        </form>
      </div>
    </div>
  );
}
