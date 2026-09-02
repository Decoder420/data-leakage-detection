import React from 'react';
import { Layers } from 'lucide-react';

export default function OverlapMatrix({ matrix, agents }) {
  if (!matrix || Object.keys(matrix).length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)' }}>
        No overlap matrix data available.
      </div>
    );
  }

  const agentIds = Object.keys(matrix);
  const getAgentName = (id) => {
    const ag = agents.find(a => a.id === id);
    return ag ? ag.name : id;
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <Layers size={18} color="var(--primary)" />
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
          Record Intersection & Overlap Matrix
        </h3>
      </div>
      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        Quantifies the exact number of shared records between the leaked data dump and each agent's distributed dataset.
      </p>

      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ minWidth: '160px' }}>Agent / Entity</th>
              <th style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#f87171', fontWeight: 700, minWidth: '120px' }}>
                🚨 LEAK DUMP
              </th>
              {agentIds.map(id => (
                <th key={id} style={{ minWidth: '130px' }}>
                  {getAgentName(id)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {agentIds.map(rowId => {
              const leakOverlap = matrix[rowId]?.['LEAK_DUMP'] || 0;
              return (
                <tr key={rowId}>
                  <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {getAgentName(rowId)}
                  </td>
                  <td style={{ 
                    backgroundColor: leakOverlap > 0 ? 'rgba(239, 68, 68, 0.1)' : 'transparent',
                    color: leakOverlap > 0 ? '#f87171' : 'var(--text-dim)',
                    fontWeight: leakOverlap > 0 ? 800 : 400
                  }}>
                    {leakOverlap} records
                  </td>
                  {agentIds.map(colId => {
                    const count = matrix[rowId]?.[colId] || 0;
                    const isSelf = rowId === colId;
                    return (
                      <td key={colId} style={{ 
                        color: isSelf ? 'var(--primary)' : 'var(--text-muted)',
                        fontWeight: isSelf ? 700 : 400,
                        backgroundColor: isSelf ? 'rgba(14, 165, 233, 0.05)' : 'transparent'
                      }}>
                        {count} {isSelf ? '(Total)' : ''}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
