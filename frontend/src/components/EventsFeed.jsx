import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Fingerprint, Search, RefreshCw, Code, CheckCircle, ExternalLink } from 'lucide-react';
import { fetchEvents } from '../api';

export default function EventsFeed() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (severityFilter) params.severity = severityFilter;
      if (typeFilter) params.event_type = typeFilter;
      const data = await fetchEvents(params);
      setEvents(data);
      if (data.length > 0 && !selectedEvent) {
        setSelectedEvent(data[0]);
      }
    } catch (e) {
      console.error('Failed to load events:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
    const interval = setInterval(loadEvents, 5000);
    return () => clearInterval(interval);
  }, [severityFilter, typeFilter]);

  const getSeverityBadge = (sev) => {
    switch (sev.toLowerCase()) {
      case 'critical': return 'badge-red';
      case 'high': return 'badge-orange';
      case 'medium': return 'badge-yellow';
      default: return 'badge-green';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="var(--primary)" />
            <h2 style={{ fontSize: '20px', fontWeight: 800 }}>DecodeX Security Events Feed</h2>
            <span className="badge badge-blue">Real-Time SOC Stream</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Standardized JSON security events emitted by the detection engine, ready for ingestion by DecodeX Threat Hunting SOC.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select className="form-select" style={{ width: 'auto', fontSize: '12px', padding: '6px 12px' }} value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select className="form-select" style={{ width: 'auto', fontSize: '12px', padding: '6px 12px' }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">All Event Types</option>
            <option value="guilt_detection">Guilt Detection</option>
            <option value="canary_triggered">Canary Triggered</option>
            <option value="leak_analysis_complete">Analysis Complete</option>
          </select>

          <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={loadEvents} disabled={loading}>
            <RefreshCw size={13} className={loading ? 'animate-spin-slow' : ''} />
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px' }}>
        {/* Events List */}
        <div className="glass-panel" style={{ padding: '16px', borderRadius: '12px', maxHeight: '680px', overflowY: 'auto' }}>
          {events.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-dim)' }}>
              No security events recorded yet. Run a leak analysis or simulated breach to generate events.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {events.map(evt => {
                const isSelected = selectedEvent && selectedEvent.event_id === evt.event_id;
                return (
                  <div
                    key={evt.event_id}
                    onClick={() => setSelectedEvent(evt)}
                    style={{
                      padding: '14px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(14, 165, 233, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                      cursor: 'pointer',
                      transition: 'all 0.15s'
                    }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span className={`badge ${getSeverityBadge(evt.severity)}`}>
                        {evt.severity.toUpperCase()}
                      </span>
                      <span className="font-mono" style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)' }}>
                      {evt.event_type.replace('_', ' ').toUpperCase()}
                    </div>
                    
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Target: <span style={{ color: 'var(--text-main)' }}>{evt.source_dataset}</span>
                    </div>

                    {evt.implicated_agent && (
                      <div style={{ fontSize: '12px', color: '#f87171', marginTop: '2px', fontWeight: 600 }}>
                        Suspect: {evt.implicated_agent} ({(evt.confidence_score * 100).toFixed(1)}%)
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Event Payload Inspector */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', height: 'fit-content' }}>
          {selectedEvent ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Code size={18} color="var(--primary)" />
                  <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Security Event JSON Payload</h3>
                </div>
                <span className="badge badge-blue">DecodeX Standard Schema</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>EVENT ID</div>
                  <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-main)', marginTop: '2px' }}>{selectedEvent.event_id}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>CONFIDENCE</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
                    {(selectedEvent.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>TIMESTAMP</div>
                  <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {selectedEvent.timestamp}
                  </div>
                </div>
              </div>

              <pre className="font-mono" style={{
                background: '#090d16',
                padding: '16px',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#38bdf8',
                overflowX: 'auto',
                maxHeight: '360px',
                border: '1px solid var(--border-color)'
              }}>
                {JSON.stringify(selectedEvent, null, 2)}
              </pre>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
              Select an event on the left to inspect its schema.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
