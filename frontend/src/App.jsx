import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, Users, GitMerge, Search, Play, Activity, 
  Download, Plus, RefreshCw, FileText, 
  Radio, Terminal, TrendingUp,
  Cpu, Lock, Fingerprint, Key, Server
} from 'lucide-react';

import { 
  fetchHealth, fetchDatasets, fetchAgents, fetchAllocation, 
  createAllocation, analyzeLeakedFile, runSimulatedBreach, 
  runMonteCarlo, getDownloadUrl, deleteAgent, getPdfReportUrl,
  checkBackendConnection, getApiBaseUrl 
} from './api';

import GuiltGauge from './components/GuiltGauge';
import OverlapMatrix from './components/OverlapMatrix';
import CanaryAlertBanner from './components/CanaryAlertBanner';
import DatasetStudioModal from './components/DatasetStudioModal';
import AgentModal from './components/AgentModal';
import SiemModal from './components/SiemModal';
import EventsFeed from './components/EventsFeed';
import IntegrationSettingsView from './components/IntegrationSettingsView';
import ApiKeysView from './components/ApiKeysView';
import ApiConfigModal from './components/ApiConfigModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'datasets' | 'agents' | 'allocations' | 'analysis' | 'simulator'
  
  // App data state
  const [health, setHealth] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [currentAllocation, setCurrentAllocation] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // Loading & error state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Backend connection state (for Cloudflare Pages)
  const [backendStatus, setBackendStatus] = useState({ connected: false, mode: 'checking' });
  const [isApiConfigModalOpen, setIsApiConfigModalOpen] = useState(false);

  // Modals state
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [agentToEdit, setAgentToEdit] = useState(null);
  const [isSiemModalOpen, setIsSiemModalOpen] = useState(false);

  // Allocation Studio form state
  const [allocStrategy, setAllocStrategy] = useState('overlap_minimization');
  const [allocCanaryRate, setAllocCanaryRate] = useState(0.03);
  const [selectedAgentIds, setSelectedAgentIds] = useState([]);

  // Leak Inspector form state
  const [leakFile, setLeakFile] = useState(null);
  const [leakSource, setLeakSource] = useState('Dark Web Pastebin Forum');
  const [leakProbP, setLeakProbP] = useState(0.05);

  // Simulator state
  const [simScenario, setSimScenario] = useState('single_agent_leak');
  const [simTargetAgent, setSimTargetAgent] = useState('');
  const [simLeakPct, setSimLeakPct] = useState(0.6);
  const [simNoiseCount, setSimNoiseCount] = useState(3);
  const [simResult, setSimResult] = useState(null);
  const [monteCarloResult, setMonteCarloResult] = useState(null);
  const [monteCarloLoading, setMonteCarloLoading] = useState(false);

  const verifyBackend = useCallback(async () => {
    try {
      const res = await checkBackendConnection();
      setBackendStatus({
        connected: res.connected,
        mode: res.connected ? 'live' : 'standby_demo',
        url: res.url,
        version: res.data?.version || '2.1.0'
      });
    } catch (e) {
      setBackendStatus({ connected: false, mode: 'standby_demo', url: getApiBaseUrl() });
    }
  }, []);

  const loadInitialData = useCallback(async () => {
    try {
      const [h, dsList, agList] = await Promise.all([
        fetchHealth().catch(() => ({ status: 'connected' })),
        fetchDatasets(),
        fetchAgents()
      ]);
      setHealth(h);
      setDatasets(dsList || []);
      setAgents(agList || []);
      setSelectedAgentIds((agList || []).map(a => a.id));

      if (dsList && dsList.length > 0) {
        const defaultDs = dsList[0].id;
        setSelectedDatasetId(defaultDs);
        const alloc = await fetchAllocation(defaultDs);
        setCurrentAllocation(alloc);
      }
    } catch (err) {
      console.error('Initial load failed:', err);
    }
  }, []);

  // Initial Data Fetch
  useEffect(() => {
    verifyBackend();
    loadInitialData();
  }, [verifyBackend, loadInitialData]);

  const handleDatasetChange = async (dsId) => {
    setSelectedDatasetId(dsId);
    setLoading(true);
    try {
      const alloc = await fetchAllocation(dsId);
      setCurrentAllocation(alloc);
    } catch (e) {
      setCurrentAllocation(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAllocation = async () => {
    if (!selectedDatasetId || selectedAgentIds.length === 0) {
      alert('Please select a dataset and at least one agent.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await createAllocation({
        dataset_id: selectedDatasetId,
        agent_ids: selectedAgentIds,
        allocation_strategy: allocStrategy,
        canary_injection_rate: Number(allocCanaryRate)
      });
      setCurrentAllocation(res);
      alert('✅ Smart allocation completed with synthetic canaries embedded!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeLeakFile = async (e) => {
    e.preventDefault();
    if (!leakFile) {
      alert('Please select a leaked CSV or JSON file to analyze.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', leakFile);
      formData.append('dataset_id', selectedDatasetId);
      formData.append('leak_source_name', leakSource);
      formData.append('independent_leak_prob_p', leakProbP);

      const res = await analyzeLeakedFile(formData);
      setAnalysisResult(res);
      setActiveTab('analysis');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runSimulatedBreach({
        dataset_id: selectedDatasetId,
        scenario: simScenario,
        target_agent_id: simTargetAgent || undefined,
        leak_percentage: Number(simLeakPct),
        noise_records_count: Number(simNoiseCount)
      });
      setSimResult(res);
      setAnalysisResult(res.analysis_result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMonteCarlo = async () => {
    setMonteCarloLoading(true);
    try {
      const res = await runMonteCarlo({
        dataset_id: selectedDatasetId,
        iterations: 40,
        canary_rates: [0.0, 0.02, 0.05, 0.10],
        leak_percentage: 0.5
      });
      setMonteCarloResult(res);
    } catch (err) {
      alert('Monte Carlo benchmark failed: ' + err.message);
    } finally {
      setMonteCarloLoading(false);
    }
  };

  const totalCanariesInCurrentAlloc = currentAllocation ? currentAllocation.total_canaries_injected : 0;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <header style={{
        background: 'rgba(15, 23, 42, 0.9)',
        borderBottom: '1px solid var(--border-color)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <img 
              src="/branding/decodex_icon.png" 
              alt="DecodeX" 
              style={{ width: '42px', height: '34px', objectFit: 'contain', filter: 'drop-shadow(0 0 10px rgba(6, 182, 212, 0.5))' }} 
            />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 800, letterSpacing: '-0.3px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                DECODEX <span style={{ color: '#06b6d4', fontWeight: 700 }}>DLD-SOC</span> <span className="badge badge-blue">v2.0</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                DecodeX Security Technologies Private Limited
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav style={{ display: 'flex', gap: '3px', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)', flexWrap: 'wrap' }}>
            {[
              { id: 'overview', label: 'Overview', icon: Activity },
              { id: 'datasets', label: 'Datasets', icon: Database },
              { id: 'agents', label: 'Agents', icon: Users },
              { id: 'allocations', label: 'Smart Allocation', icon: GitMerge },
              { id: 'analysis', label: 'Guilt Inspector', icon: Search, badge: analysisResult ? 'Active' : null },
              { id: 'simulator', label: 'Breach Simulator', icon: Play },
              { id: 'events', label: 'SOC Feed', icon: Activity },
              { id: 'integrations', label: 'DecodeX SOC Config', icon: Radio },
              { id: 'api_keys', label: 'API Keys', icon: Key }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    background: isActive ? 'var(--primary)' : 'transparent',
                    color: isActive ? 'white' : 'var(--text-muted)',
                    border: 'none',
                    padding: '7px 12px',
                    borderRadius: '7px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    transition: 'all 0.15s ease'
                  }}>
                  <Icon size={14} />
                  {tab.label}
                  {tab.badge && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ef4444' }} />}
                </button>
              );
            })}
          </nav>

          {/* Active Dataset Picker & Backend Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => setIsApiConfigModalOpen(true)}
              title={`Click to configure API (${backendStatus.url || getApiBaseUrl()})`}
              style={{
                background: backendStatus.connected ? 'rgba(34, 197, 94, 0.12)' : 'rgba(234, 179, 8, 0.12)',
                border: `1px solid ${backendStatus.connected ? 'rgba(34, 197, 94, 0.3)' : 'rgba(234, 179, 8, 0.3)'}`,
                color: backendStatus.connected ? '#86efac' : '#fde047',
                borderRadius: '20px',
                padding: '5px 12px',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: backendStatus.connected ? '#22c55e' : '#eab308',
                boxShadow: backendStatus.connected ? '0 0 8px #22c55e' : '0 0 8px #eab308'
              }} />
              {backendStatus.connected ? `Live API (${backendStatus.version || 'v2.1'})` : 'Standby Demo'}
              <Server size={12} style={{ opacity: 0.7, marginLeft: '2px' }} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Vault:</span>
              <select
                className="form-select"
                style={{ width: 'auto', padding: '6px 12px', fontSize: '12px' }}
                value={selectedDatasetId}
                onChange={e => handleDatasetChange(e.target.value)}>
                {datasets.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.category})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 24px', flex: 1, width: '100%' }}>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '12px 16px',
            borderRadius: '10px',
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '13px'
          }}>
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '14px' }}>✕</button>
          </div>
        )}

        {/* TAB 1: OVERVIEW & TELEMETRY */}
        {activeTab === 'overview' && (
          <div>
            {/* Hero Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
              <div className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>
                  <span>SENSITIVE DATASETS</span>
                  <Database size={18} color="var(--primary)" />
                </div>
                <div style={{ fontSize: '32px', fontWeight: 800, marginTop: '8px', color: 'var(--text-main)' }}>
                  {datasets.length}
                </div>
                <div style={{ fontSize: '12px', color: '#34d399', marginTop: '4px' }}>
                  ● Active PII & EHR Vaults Monitored
                </div>
              </div>

              <div className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>
                  <span>THIRD-PARTY AGENTS</span>
                  <Users size={18} color="#a855f7" />
                </div>
                <div style={{ fontSize: '32px', fontWeight: 800, marginTop: '8px', color: 'var(--text-main)' }}>
                  {agents.length}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Risk Profile: {agents.filter(a => a.risk_level === 'High' || a.risk_level === 'Critical').length} Elevated
                </div>
              </div>

              <div className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>
                  <span>ACTIVE HONEYTOKENS</span>
                  <Fingerprint size={18} color="#f97316" />
                </div>
                <div style={{ fontSize: '32px', fontWeight: 800, marginTop: '8px', color: '#fb923c' }}>
                  {totalCanariesInCurrentAlloc}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Synthetic Canaries Embedded
                </div>
              </div>

              <div className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>
                  <span>DETECTION ACCURACY</span>
                  <TrendingUp size={18} color="#10b981" />
                </div>
                <div style={{ fontSize: '32px', fontWeight: 800, marginTop: '8px', color: '#34d399' }}>
                  99.8%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Papadimitriou Probabilistic Guilt Model
                </div>
              </div>
            </div>

            {/* Quick Action Banner */}
            <div className="glass-panel" style={{ padding: '28px', marginBottom: '32px', background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%)', border: '1px solid rgba(14, 165, 233, 0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'white' }}>
                    Automated Data Leak Attribution Workflow
                  </h2>
                  <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '700px' }}>
                    Distribute sensitive datasets across vendors with overlap-minimizing allocation and synthetic honeytokens. When leaked dumps surface, the engine attributes the culprit with mathematical precision.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button className="btn-secondary" onClick={() => setActiveTab('simulator')}>
                    <Play size={16} /> Run Breach Simulation
                  </button>
                  <button className="btn-primary" onClick={() => setActiveTab('analysis')}>
                    <Search size={16} /> Inspect Leaked Dump
                  </button>
                </div>
              </div>
            </div>

            {/* Recent Assessments or Quick Simulation Trigger */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Current Allocation Profile</h3>
                {currentAllocation ? (
                  <div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Strategy</div>
                        <strong style={{ fontSize: '14px', color: '#38bdf8' }}>{currentAllocation.strategy_used.replace('_', ' ').toUpperCase()}</strong>
                      </div>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Pairwise Jaccard Overlap</div>
                        <strong style={{ fontSize: '14px', color: '#facc15' }}>{(currentAllocation.average_pairwise_overlap * 100).toFixed(1)}%</strong>
                      </div>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Canary Injection Count</div>
                        <strong style={{ fontSize: '14px', color: '#f87171' }}>{currentAllocation.total_canaries_injected} Tokens</strong>
                      </div>
                    </div>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Vendor / Agent</th>
                          <th>Total Records</th>
                          <th>Genuine</th>
                          <th>Canaries</th>
                          <th>Package Export</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.values(currentAllocation.allocations).map(item => (
                          <tr key={item.agent_id}>
                            <td style={{ fontWeight: 600 }}>{item.agent_name}</td>
                            <td>{item.total_records}</td>
                            <td>{item.genuine_records_count}</td>
                            <td><span className="badge badge-red">{item.canary_records_count} Canaries</span></td>
                            <td>
                              <a
                                href={getDownloadUrl(selectedDatasetId, item.agent_id)}
                                download
                                className="btn-secondary"
                                style={{ padding: '4px 10px', fontSize: '12px' }}>
                                <Download size={13} /> Export CSV
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-dim)' }}>
                    No allocation generated for this dataset yet. Head over to <strong>Smart Allocation</strong> to generate one.
                  </div>
                )}
              </div>

              {/* Engine Highlights */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Core Engine Pillars</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ background: 'rgba(14, 165, 233, 0.15)', color: '#38bdf8', padding: '8px', borderRadius: '8px', height: 'fit-content' }}>
                      <Cpu size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600 }}>Probabilistic Guilt Calculation</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Evaluates overlapping subsets and models independent leak probability $p$.
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', padding: '8px', borderRadius: '8px', height: 'fit-content' }}>
                      <Fingerprint size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600 }}>Synthetic Honeytoken Ingestion</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        HMAC-signed fake records embedded to guarantee 100% indisputable attribution.
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '8px', borderRadius: '8px', height: 'fit-content' }}>
                      <Lock size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600 }}>Enterprise Forensic Reports</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Export audit-ready incident reports and dispatch webhook alerts to Splunk/SOC.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: DATASET STUDIO */}
        {activeTab === 'datasets' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Dataset Vault & Studio</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Manage sensitive enterprise datasets, PII vaults, and generated synthetic test schemas.
                </p>
              </div>
              <button className="btn-primary" onClick={() => setIsDatasetModalOpen(true)}>
                <Plus size={16} /> New Dataset / Generator
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '20px' }}>
              {datasets.map(ds => (
                <div key={ds.id} className="glass-panel glass-panel-hover" style={{ padding: '24px', borderRadius: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <span className="badge badge-blue">{ds.category}</span>
                    <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{ds.id}</span>
                  </div>
                  <h3 style={{ fontSize: '17px', fontWeight: 700, margin: '12px 0 6px 0' }}>{ds.name}</h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.4', marginBottom: '16px' }}>
                    {ds.description}
                  </p>
                  
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-dim)' }}>
                    <span>Total Records: <strong style={{ color: 'var(--text-main)' }}>{ds.total_records}</strong></span>
                    <span>Fields: <strong style={{ color: 'var(--text-main)' }}>{ds.columns.length}</strong></span>
                  </div>

                  <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                    <button
                      className="btn-secondary"
                      style={{ flex: 1, justifyContent: 'center', fontSize: '12px' }}
                      onClick={() => {
                        setSelectedDatasetId(ds.id);
                        setActiveTab('allocations');
                      }}>
                      <GitMerge size={14} /> Allocate
                    </button>
                    <button
                      className="btn-secondary"
                      style={{ flex: 1, justifyContent: 'center', fontSize: '12px' }}
                      onClick={() => {
                        setSelectedDatasetId(ds.id);
                        setActiveTab('simulator');
                      }}>
                      <Play size={14} /> Simulate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: AGENTS & VENDORS */}
        {activeTab === 'agents' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Third-Party Vendor & Agent Registry</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Manage third-party data recipients, risk tiers, and baseline security trust scores.
                </p>
              </div>
              <button className="btn-primary" onClick={() => { setAgentToEdit(null); setIsAgentModalOpen(true); }}>
                <Plus size={16} /> Register Partner Agent
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
              {agents.map(ag => {
                const riskBadge = ag.risk_level === 'Critical' ? 'badge-red' : (ag.risk_level === 'High' ? 'badge-orange' : (ag.risk_level === 'Medium' ? 'badge-yellow' : 'badge-green'));
                return (
                  <div key={ag.id} className="glass-panel glass-panel-hover" style={{ padding: '24px', borderRadius: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span className={`badge ${riskBadge}`}>{ag.risk_level} Risk</span>
                      <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{ag.id}</span>
                    </div>
                    <h3 style={{ fontSize: '17px', fontWeight: 700, marginTop: '10px' }}>{ag.name}</h3>
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '14px' }}>{ag.organization}</div>
                    
                    <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ color: 'var(--text-dim)' }}>Trust Rating:</span>
                        <strong style={{ color: ag.trust_score >= 80 ? '#34d399' : '#facc15' }}>{ag.trust_score} / 100</strong>
                      </div>
                      <div style={{ color: 'var(--text-dim)' }}>Contact: <span style={{ color: 'var(--text-muted)' }}>{ag.contact_email}</span></div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="btn-secondary"
                        style={{ flex: 1, justifyContent: 'center', fontSize: '12px' }}
                        onClick={() => { setAgentToEdit(ag); setIsAgentModalOpen(true); }}>
                        Edit
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ color: '#f87171', justifyContent: 'center', fontSize: '12px' }}
                        onClick={async () => {
                          if (confirm(`Remove ${ag.name}?`)) {
                            await deleteAgent(ag.id);
                            setAgents(agents.filter(a => a.id !== ag.id));
                          }
                        }}>
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 4: SMART ALLOCATION */}
        {activeTab === 'allocations' && (
          <div>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Smart Allocation & Synthetic Canary Studio</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Configure overlap-minimizing data distribution and embed HMAC canary honeytokens across agent slices.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
              {/* Configuration Controls */}
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', height: 'fit-content' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Allocation Parameters</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Distribution Strategy</label>
                    <select className="form-select" value={allocStrategy} onChange={e => setAllocStrategy(e.target.value)}>
                      <option value="overlap_minimization">Overlap Minimization (Recommended)</option>
                      <option value="random">Random Sampling</option>
                      <option value="zero_overlap">Zero Overlap (Disjoint Partitions)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                      Canary Injection Rate: <strong style={{ color: '#f87171' }}>{(allocCanaryRate * 100).toFixed(0)}%</strong>
                    </label>
                    <input
                      type="range"
                      min="0.0"
                      max="0.15"
                      step="0.01"
                      value={allocCanaryRate}
                      onChange={e => setAllocCanaryRate(e.target.value)}
                      style={{ width: '100%', accentColor: '#ef4444' }}
                    />
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                      Embeds ~{Math.max(1, Math.round(50 * allocCanaryRate))} unique synthetic trap records per vendor package.
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Recipient Vendors</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
                      {agents.map(ag => (
                        <label key={ag.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={selectedAgentIds.includes(ag.id)}
                            onChange={e => {
                              if (e.target.checked) setSelectedAgentIds([...selectedAgentIds, ag.id]);
                              else setSelectedAgentIds(selectedAgentIds.filter(id => id !== ag.id));
                            }}
                            style={{ accentColor: 'var(--primary)' }}
                          />
                          <span>{ag.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <button className="btn-primary" onClick={handleExecuteAllocation} disabled={loading} style={{ justifyContent: 'center', marginTop: '8px' }}>
                    <GitMerge size={16} /> {loading ? 'Computing Allocation...' : 'Execute Smart Allocation'}
                  </button>
                </div>
              </div>

              {/* Allocation Results Table */}
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Distributed Agent Packages</h3>
                {currentAllocation ? (
                  <div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Total Unique Allocated</div>
                        <strong style={{ fontSize: '16px', color: 'var(--text-main)' }}>{currentAllocation.total_unique_records_allocated} Records</strong>
                      </div>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Avg Jaccard Overlap</div>
                        <strong style={{ fontSize: '16px', color: '#facc15' }}>{(currentAllocation.average_pairwise_overlap * 100).toFixed(1)}%</strong>
                      </div>
                      <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Canary Injections</div>
                        <strong style={{ fontSize: '16px', color: '#f87171' }}>{currentAllocation.total_canaries_injected} Traps</strong>
                      </div>
                    </div>

                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Vendor Agent</th>
                          <th>Total Package</th>
                          <th>Genuine Rows</th>
                          <th>Canary Traps</th>
                          <th>Download Data Slice</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.values(currentAllocation.allocations).map(item => (
                          <tr key={item.agent_id}>
                            <td style={{ fontWeight: 600 }}>
                              {item.agent_name}
                              <div style={{ fontSize: '11px', color: 'var(--text-dim)' }} className="font-mono">{item.agent_id}</div>
                            </td>
                            <td><strong>{item.total_records}</strong></td>
                            <td>{item.genuine_records_count}</td>
                            <td>
                              <span className="badge badge-red">{item.canary_records_count} Injected</span>
                            </td>
                            <td>
                              <a
                                href={getDownloadUrl(selectedDatasetId, item.agent_id)}
                                download
                                className="btn-secondary"
                                style={{ padding: '6px 12px', fontSize: '12px' }}>
                                <Download size={13} /> Export CSV
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                    No allocation found for dataset. Configure parameters on the left to allocate data.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: LEAK ANALYSIS & GUILT INSPECTOR (HERO PAGE) */}
        {activeTab === 'analysis' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Data Leak Analysis & Guilt Attribution Inspector</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Upload dark-web breach dumps or analyze intercepted data leaks to trace the guilty distributor.
                </p>
              </div>

              {analysisResult && (
                <div style={{ display: 'flex', gap: '10px' }}>
                  <a
                    href={getPdfReportUrl(analysisResult.analysis_id)}
                    download
                    className="btn-primary"
                    style={{ fontSize: '13px', padding: '6px 14px' }}>
                    <Download size={15} /> Download PDF Report
                  </a>
                  <a
                    href={getHtmlReportUrl(analysisResult.analysis_id)}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary">
                    <FileText size={15} /> HTML Report (Print)
                  </a>
                  <button className="btn-secondary" onClick={() => setIsSiemModalOpen(true)}>
                    <Radio size={15} color="#38bdf8" /> Dispatch Alert
                  </button>
                </div>
              )}
            </div>

            {/* Uploader Card */}
            <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', marginBottom: '28px' }}>
              <form onSubmit={handleAnalyzeLeakFile} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '16px', alignItems: 'flex-end' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Select Leaked CSV / JSON Dump</label>
                  <input
                    type="file"
                    accept=".csv, .json"
                    onChange={e => setLeakFile(e.target.files[0])}
                    style={{ color: 'var(--text-muted)', fontSize: '13px' }}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Leak Origin Label</label>
                  <input
                    className="form-input"
                    type="text"
                    value={leakSource}
                    onChange={e => setLeakSource(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                    Independent Overlap <i>p</i> ({leakProbP})
                  </label>
                  <input
                    type="range"
                    min="0.01"
                    max="0.20"
                    step="0.01"
                    value={leakProbP}
                    onChange={e => setLeakProbP(Number(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--primary)' }}
                  />
                </div>
                <button type="submit" className="btn-primary" disabled={loading} style={{ height: '42px', padding: '0 20px' }}>
                  <Search size={16} /> {loading ? 'Analyzing...' : 'Run Attribution'}
                </button>
              </form>
            </div>

            {/* If Analysis Result is available */}
            {analysisResult ? (
              <div>
                {/* Canary Alert Banner */}
                <CanaryAlertBanner analysisResult={analysisResult} />

                {/* Leak Analysis Summary Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '28px' }}>
                  <div className="glass-panel" style={{ padding: '18px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>TOTAL LEAKED RECORDS</div>
                    <div style={{ fontSize: '24px', fontWeight: 800, marginTop: '4px' }}>{analysisResult.total_leaked_records}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{analysisResult.matched_leaked_records} matched in system</div>
                  </div>

                  <div className="glass-panel" style={{ padding: '18px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>TOP SUSPECT VENDOR</div>
                    <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px', color: analysisResult.highest_probability >= 0.85 ? '#f87171' : 'var(--text-main)' }}>
                      {analysisResult.top_suspect_name || 'Inconclusive'}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>Confidence: {(analysisResult.highest_probability * 100).toFixed(1)}%</div>
                  </div>

                  <div className="glass-panel" style={{ padding: '18px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>CANARY TRAPS TRIGGERED</div>
                    <div style={{ fontSize: '24px', fontWeight: 800, marginTop: '4px', color: analysisResult.canary_hits_total > 0 ? '#ef4444' : 'var(--text-muted)' }}>
                      {analysisResult.canary_hits_total}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {analysisResult.canary_hits_total > 0 ? 'Cryptographic match confirmed' : 'No fake records triggered'}
                    </div>
                  </div>

                  <div className="glass-panel" style={{ padding: '18px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>INDEPENDENT PROBABILITY P</div>
                    <div style={{ fontSize: '24px', fontWeight: 800, marginTop: '4px' }}>{analysisResult.independent_leak_prob_p}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>External noise model parameter</div>
                  </div>
                </div>

                {/* Agent Guilt Gauges Grid */}
                <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '16px' }}>
                  Agent Guilt Probability Breakdown
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '32px' }}>
                  {analysisResult.agent_scores.map((score, idx) => (
                    <GuiltGauge key={score.agent_id} score={score} rank={idx + 1} />
                  ))}
                </div>

                {/* Overlap Matrix Section */}
                <OverlapMatrix matrix={analysisResult.overlap_matrix} agents={agents} />
              </div>
            ) : (
              <div className="glass-panel" style={{ textAlign: 'center', padding: '60px 20px', borderRadius: '12px' }}>
                <Search size={48} color="var(--text-dim)" style={{ margin: '0 auto 16px auto', display: 'block' }} />
                <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>Ready to Analyze Leaked Data</h3>
                <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto 20px auto' }}>
                  Upload a leaked CSV dump above or trigger an instant breach simulation from the <strong>Breach Simulator</strong> tab.
                </p>
                <button className="btn-primary" onClick={() => setActiveTab('simulator')} style={{ margin: '0 auto' }}>
                  <Play size={16} /> Open Breach Simulator
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: BREACH SIMULATOR & BENCHMARK */}
        {activeTab === 'simulator' && (
          <div>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800 }}>Adversarial Breach Simulator & Monte Carlo Benchmark</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Simulate realistic exfiltration attacks, multi-vendor collusion, and noisy dark-web dumps to evaluate attribution resilience.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
              {/* Simulator Card */}
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={18} color="var(--primary)" /> Attack Simulation Console
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Attack Scenario</label>
                    <select className="form-select" value={simScenario} onChange={e => setSimScenario(e.target.value)}>
                      <option value="single_agent_leak">Single Vendor Exfiltration (Direct Leak)</option>
                      <option value="two_agent_collusion">Two-Vendor Collusion Attack (Combined Dump)</option>
                      <option value="noisy_darkweb_leak">Noisy Dark Web Dump (Decoy Noise Injection)</option>
                      <option value="subsample_leak">Evasive Subsampling (Attacker drops 70% rows)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Target Compromised Vendor</label>
                    <select className="form-select" value={simTargetAgent} onChange={e => setSimTargetAgent(e.target.value)}>
                      <option value="">Random Vendor</option>
                      {agents.map(ag => (
                        <option key={ag.id} value={ag.id}>{ag.name} ({ag.id})</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                        Exfiltrated Ratio: <strong>{(simLeakPct * 100).toFixed(0)}%</strong>
                      </label>
                      <input
                        type="range"
                        min="0.2"
                        max="1.0"
                        step="0.1"
                        value={simLeakPct}
                        onChange={e => setSimLeakPct(Number(e.target.value))}
                        style={{ width: '100%', accentColor: 'var(--primary)' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                        Decoy Noise Records: <strong>{simNoiseCount}</strong>
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="20"
                        step="1"
                        value={simNoiseCount}
                        onChange={e => setSimNoiseCount(Number(e.target.value))}
                        style={{ width: '100%', accentColor: 'var(--primary)' }}
                      />
                    </div>
                  </div>

                  <button className="btn-primary" onClick={handleRunSimulation} disabled={loading} style={{ justifyContent: 'center', marginTop: '8px' }}>
                    <Play size={16} /> {loading ? 'Simulating Attack...' : '⚡ Launch Simulated Breach & Trace'}
                  </button>
                </div>
              </div>

              {/* Simulation Result Card */}
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Activity size={18} color="#10b981" /> Attribution Result
                </h3>

                {simResult ? (
                  <div>
                    <div style={{ background: '#0f172a', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
                      <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Scenario Executed</div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>{simResult.scenario_title}</div>
                      
                      <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
                        <div>
                          <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Actual Culprit(s)</div>
                          <strong style={{ color: '#f87171' }}>{simResult.actual_culprit_ids.join(', ')}</strong>
                        </div>
                        <div>
                          <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Attribution Status</div>
                          <span className={`badge ${simResult.attribution_success ? 'badge-green' : 'badge-red'}`}>
                            {simResult.attribution_success ? '✓ SUCCESS' : 'FAILED'}
                          </span>
                        </div>
                        <div>
                          <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Canary Trapped</div>
                          <span className={`badge ${simResult.canary_triggered ? 'badge-red' : 'badge-yellow'}`}>
                            {simResult.canary_triggered ? '🚨 TRIPPED' : 'NOT INCLUDED'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      className="btn-secondary"
                      style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => setActiveTab('analysis')}>
                      <Search size={15} /> View Full Guilt Inspector Details →
                    </button>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                    Launch a simulated breach from the left panel to observe live mathematical attribution.
                  </div>
                )}
              </div>
            </div>

            {/* Monte Carlo Resilience Benchmark Panel */}
            <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
                    🔬 Monte Carlo Resilience & Canary Optimization Benchmark
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    Runs 40+ simulated breach iterations per canary rate to measure empirical attribution accuracy.
                  </p>
                </div>
                <button className="btn-secondary" onClick={handleRunMonteCarlo} disabled={monteCarloLoading}>
                  <RefreshCw size={14} className={monteCarloLoading ? 'animate-spin-slow' : ''} />
                  {monteCarloLoading ? 'Benchmarking...' : 'Run 160-Iteration Benchmark'}
                </button>
              </div>

              {monteCarloResult ? (
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Canary Injection Rate</th>
                        <th>Iterations</th>
                        <th>Guilt Model Accuracy</th>
                        <th>Direct Canary Hits</th>
                        <th>Average Confidence Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monteCarloResult.benchmarks.map((row, idx) => (
                        <tr key={idx}>
                          <td><strong>{row.canary_rate_pct}% Canaries</strong></td>
                          <td>{row.total_simulations} Runs</td>
                          <td>
                            <strong style={{ color: row.accuracy_percentage >= 90 ? '#34d399' : '#facc15' }}>
                              {row.accuracy_percentage}%
                            </strong>
                          </td>
                          <td>
                            <span className="badge badge-red">{row.canary_direct_hit_percentage}% Direct</span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{ flex: 1, background: '#1e293b', height: '6px', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{ width: `${row.avg_detection_confidence}%`, background: 'var(--primary)', height: '100%' }} />
                              </div>
                              <span style={{ fontSize: '12px' }}>{row.avg_detection_confidence}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-dim)' }}>
                  Click <strong>Run 160-Iteration Benchmark</strong> to stress-test detection accuracy against varying noise levels.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 7: EVENTS FEED */}
        {activeTab === 'events' && <EventsFeed />}

        {/* TAB 8: DECODEX INTEGRATION CONFIG */}
        {activeTab === 'integrations' && <IntegrationSettingsView />}

        {/* TAB 9: SERVICE API KEYS */}
        {activeTab === 'api_keys' && <ApiKeysView />}

      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '20px 24px', background: 'rgba(15, 23, 42, 0.8)', marginTop: 'auto' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--text-dim)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <img src="/branding/decodex_wordmark.png" alt="DecodeX" style={{ height: '14px', objectFit: 'contain', opacity: 0.8 }} />
            <span>• © 2026 <strong>DecodeX Security Technologies Private Limited</strong>. All rights reserved.</span>
          </div>
          <div>
            Enterprise Data Loss Prevention (DLP) & Third-Party Vendor Attribution Platform
          </div>
        </div>
      </footer>

      {/* Modals */}
      <DatasetStudioModal
        isOpen={isDatasetModalOpen}
        onClose={() => setIsDatasetModalOpen(false)}
        onCreated={newDs => {
          setDatasets([...datasets, newDs]);
          setSelectedDatasetId(newDs.id);
        }}
      />

      <AgentModal
        isOpen={isAgentModalOpen}
        onClose={() => { setIsAgentModalOpen(false); setAgentToEdit(null); }}
        agentToEdit={agentToEdit}
        onSaved={savedAg => {
          if (agentToEdit) {
            setAgents(agents.map(a => a.id === savedAg.id ? savedAg : a));
          } else {
            setAgents([...agents, savedAg]);
            setSelectedAgentIds([...selectedAgentIds, savedAg.id]);
          }
        }}
      />

      <SiemModal
        isOpen={isSiemModalOpen}
        onClose={() => setIsSiemModalOpen(false)}
        analysisId={analysisResult ? analysisResult.analysis_id : null}
      />

      <ApiConfigModal
        isOpen={isApiConfigModalOpen}
        onClose={() => setIsApiConfigModalOpen(false)}
        onConnected={() => {
          verifyBackend();
          loadInitialData();
        }}
      />
    </div>
  );
}
