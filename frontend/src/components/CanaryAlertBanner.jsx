import React, { useEffect } from 'react';
import { Fingerprint, ShieldAlert, Zap } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function CanaryAlertBanner({ analysisResult }) {
  useEffect(() => {
    if (!analysisResult || !analysisResult.canary_hits_total) return;
    // Fire celebratory detection confetti
    try {
      confetti({
        particleCount: 70,
        spread: 60,
        origin: { y: 0.7 },
        colors: ['#ef4444', '#f97316', '#38bdf8']
      });
    } catch (e) {
      // ignore
    }
  }, [analysisResult?.analysis_id, analysisResult?.canary_hits_total]);

  if (!analysisResult || analysisResult.canary_hits_total === 0) return null;

  const confirmedAgent = analysisResult.top_suspect_name || analysisResult.canary_confirmed_agent_id;

  return (
    <div className="glass-panel alert-pulse" style={{
      padding: '20px 24px',
      borderRadius: '12px',
      border: '1px solid #ef4444',
      background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%)',
      marginBottom: '24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{
            background: '#ef4444',
            color: 'white',
            width: '48px',
            height: '48px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <Fingerprint size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-red">🚨 ZERO-DENIABILITY ATTRIBUTION</span>
              <span style={{ fontSize: '12px', color: '#fca5a5' }}>Cryptographic Proof Verified</span>
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'white', marginTop: '6px' }}>
              Canary Honeytoken Triggered: {confirmedAgent}
            </h2>
            <p style={{ fontSize: '13px', color: '#e2e8f0', marginTop: '4px', maxWidth: '750px', lineHeight: '1.5' }}>
              A synthetic canary record injected exclusively into <strong>{confirmedAgent}</strong>'s distributed dataset package was detected inside the unauthorized leak dump. This provides <strong>100% mathematical and forensic certainty</strong> of breach attribution.
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Canary Traps Tripped</div>
          <div style={{ fontSize: '28px', fontWeight: 900, color: '#f87171' }}>
            {analysisResult.canary_hits_total}
          </div>
        </div>
      </div>
    </div>
  );
}
