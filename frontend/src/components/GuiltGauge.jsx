import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle, Fingerprint } from 'lucide-react';

export default function GuiltGauge({ score, rank }) {
  const prob = score.guilt_probability;
  const pct = Math.round(prob * 100);

  // Color selection based on verdict and probability
  let strokeColor = '#22c55e'; // green
  let badgeClass = 'badge-green';
  let Icon = ShieldCheck;

  if (score.verdict === 'CONFIRMED_LEAKER' || score.canary_records_found > 0) {
    strokeColor = '#ef4444'; // red
    badgeClass = 'badge-red';
    Icon = Fingerprint;
  } else if (prob >= 0.85) {
    strokeColor = '#f97316'; // orange
    badgeClass = 'badge-orange';
    Icon = ShieldAlert;
  } else if (prob >= 0.40) {
    strokeColor = '#eab308'; // yellow
    badgeClass = 'badge-yellow';
    Icon = AlertTriangle;
  }

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (prob * circumference);

  return (
    <div className={`glass-panel p-4 flex flex-col justify-between relative overflow-hidden ${score.canary_records_found > 0 ? 'border-red-500/50 shadow-lg shadow-red-500/10 alert-pulse' : ''}`}
         style={{ padding: '20px', borderRadius: '12px', border: score.canary_records_found > 0 ? '1px solid rgba(239, 68, 68, 0.6)' : '1px solid var(--border-color)' }}>
      
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Suspect #{rank}
          </div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
            {score.agent_name}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            ID: <span className="font-mono">{score.agent_id}</span>
          </div>
        </div>

        <span className={`badge ${badgeClass}`}>
          <Icon size={13} /> {score.verdict.replace('_', ' ')}
        </span>
      </div>

      {/* Middle Gauge & Stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', margin: '12px 0' }}>
        {/* SVG Circle Gauge */}
        <div style={{ position: 'relative', width: '92px', height: '92px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="92" height="92" viewBox="0 0 92 92" style={{ transform: 'rotate(-90deg)' }}>
            <circle
              cx="46"
              cy="46"
              r={radius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="8"
              fill="transparent"
            />
            <circle
              cx="46"
              cy="46"
              r={radius}
              stroke={strokeColor}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
          </svg>
          <div style={{ position: 'absolute', textAlign: 'center' }}>
            <div style={{ fontSize: '18px', fontWeight: 800, color: strokeColor }}>
              {pct}%
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Guilt
            </div>
          </div>
        </div>

        {/* Breakdown Stats */}
        <div style={{ flex: 1, fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Matched Records:</span>
            <strong style={{ color: 'var(--text-main)' }}>{score.matching_records_count}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Genuine Matches:</span>
            <strong style={{ color: 'var(--text-main)' }}>{score.matching_genuine_count}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Canary Traps:</span>
            <strong style={{ color: score.canary_records_found > 0 ? '#ef4444' : 'var(--text-main)' }}>
              {score.canary_records_found > 0 ? `🚨 ${score.canary_records_found} Hit` : '0'}
            </strong>
          </div>
        </div>
      </div>

      {/* Forensic Explanation */}
      <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '6px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
        {score.explanation}
      </div>

      {/* Triggered Canary Token Tag (if any) */}
      {score.triggered_canary_tokens && score.triggered_canary_tokens.length > 0 && (
        <div style={{ marginTop: '8px', padding: '6px 10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', fontSize: '11px', color: '#f87171' }}>
          <strong>Trap Token:</strong> <span className="font-mono">{score.triggered_canary_tokens.join(', ')}</span>
        </div>
      )}
    </div>
  );
}
