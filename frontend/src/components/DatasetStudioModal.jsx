import React, { useState } from 'react';
import { X, Sparkles, Upload, Database } from 'lucide-react';
import { generateDataset, uploadDataset } from '../api';

export default function DatasetStudioModal({ isOpen, onClose, onCreated }) {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState('generate'); // 'generate' | 'upload'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Generate form state
  const [genName, setGenName] = useState('Enterprise Client Portfolio');
  const [genCategory, setGenCategory] = useState('Fintech');
  const [genCount, setGenCount] = useState(100);

  // Upload form state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadCategory, setUploadCategory] = useState('Fintech');

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await generateDataset({
        name: genName,
        category: genCategory,
        num_records: Number(genCount)
      });
      onCreated(res);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setError('Please select a CSV or JSON file.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('name', uploadName || uploadFile.name);
      formData.append('category', uploadCategory);
      
      const res = await uploadDataset(formData);
      onCreated(res);
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
        maxWidth: '540px',
        padding: '28px',
        borderRadius: '16px',
        border: '1px solid var(--border-color)',
        background: '#0f172a'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={20} color="var(--primary)" />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Dataset Studio</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveTab('generate')}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              background: activeTab === 'generate' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'generate' ? 'white' : 'var(--text-muted)'
            }}>
            <Sparkles size={14} /> 1-Click Generator
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              background: activeTab === 'upload' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'upload' ? 'white' : 'var(--text-muted)'
            }}>
            <Upload size={14} /> Upload Custom File
          </button>
        </div>

        {error && (
          <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '8px', color: '#f87171', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {/* Generate Form */}
        {activeTab === 'generate' ? (
          <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Dataset Name</label>
              <input
                className="form-input"
                type="text"
                value={genName}
                onChange={e => setGenName(e.target.value)}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Industry / Category</label>
              <select className="form-select" value={genCategory} onChange={e => setGenCategory(e.target.value)}>
                <option value="Fintech">Fintech (Banking, SSNs, Wealth Management)</option>
                <option value="Healthcare">Healthcare (HIPAA EHR, Diagnoses)</option>
                <option value="Enterprise HR">Enterprise HR (Salaries, Clearances)</option>
                <option value="E-Commerce">E-Commerce (Customer PII, Orders)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Total Records Count ({genCount})</label>
              <input
                type="range"
                min="20"
                max="300"
                step="10"
                value={genCount}
                onChange={e => setGenCount(e.target.value)}
                style={{ width: '100%', accentColor: 'var(--primary)' }}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '8px' }}>
              {loading ? 'Generating...' : '✨ Generate Synthetic Dataset'}
            </button>
          </form>
        ) : (
          /* Upload Form */
          <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Select CSV or JSON File</label>
              <input
                type="file"
                accept=".csv, .json"
                onChange={e => setUploadFile(e.target.files[0])}
                style={{ color: 'var(--text-muted)', fontSize: '13px' }}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Dataset Name</label>
              <input
                className="form-input"
                type="text"
                placeholder="e.g. Q3 Customer Master List"
                value={uploadName}
                onChange={e => setUploadName(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Category</label>
              <select className="form-select" value={uploadCategory} onChange={e => setUploadCategory(e.target.value)}>
                <option value="Fintech">Fintech</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Enterprise HR">Enterprise HR</option>
                <option value="E-Commerce">E-Commerce</option>
              </select>
            </div>
            <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '8px' }}>
              {loading ? 'Uploading...' : '📁 Upload Dataset'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
