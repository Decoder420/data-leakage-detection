/**
 * Frontend API client for DecodeX DLD-SOC Platform (/api/v1 & legacy).
 * DecodeX Security Technologies Private Limited.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  return res.json();
}

export async function fetchDatasets() {
  const res = await fetch(`${API_BASE}/api/v1/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function fetchDatasetDetails(id) {
  const res = await fetch(`${API_BASE}/api/v1/datasets/${id}`);
  if (!res.ok) throw new Error('Failed to fetch dataset details');
  return res.json();
}

export async function generateDataset(payload) {
  const res = await fetch(`${API_BASE}/api/v1/datasets/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to generate dataset');
  return res.json();
}

export async function uploadDataset(formData) {
  const res = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload dataset');
  return res.json();
}

export async function fetchAgents() {
  const res = await fetch(`${API_BASE}/api/v1/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

export async function createAgent(payload) {
  const res = await fetch(`${API_BASE}/api/v1/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create agent');
  return res.json();
}

export async function updateAgent(id, payload) {
  const res = await fetch(`${API_BASE}/api/v1/agents/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update agent');
  return res.json();
}

export async function deleteAgent(id) {
  const res = await fetch(`${API_BASE}/api/v1/agents/${id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete agent');
  return res.json();
}

export async function createAllocation(config) {
  const res = await fetch(`${API_BASE}/api/v1/distribute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create allocation');
  }
  return res.json();
}

export function getDownloadUrl(allocationId, agentId) {
  return `${API_BASE}/api/v1/distribute/${allocationId}/agent/${agentId}/download`;
}

export async function analyzeLeakedFile(formData) {
  const res = await fetch(`${API_BASE}/api/v1/analyze/file`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to analyze leaked file');
  }
  return res.json();
}

export async function analyzeLeakedJson(payload) {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to analyze leaked JSON');
  }
  return res.json();
}

export async function fetchEvents(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/v1/events?${query}`);
  if (!res.ok) throw new Error('Failed to fetch security events');
  return res.json();
}

export async function fetchIntegrationSettings() {
  const res = await fetch(`${API_BASE}/api/v1/integrations`);
  if (!res.ok) throw new Error('Failed to fetch integration settings');
  return res.json();
}

export async function updateIntegrationSettings(payload) {
  const res = await fetch(`${API_BASE}/api/v1/integrations`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update integration settings');
  return res.json();
}

export async function testSocConnection() {
  const res = await fetch(`${API_BASE}/api/v1/integrations/test`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to test SOC connection');
  return res.json();
}

export async function fetchApiKeys() {
  const res = await fetch(`${API_BASE}/api/v1/api-keys`);
  if (!res.ok) throw new Error('Failed to fetch API keys');
  return res.json();
}

export async function createApiKey(payload) {
  const res = await fetch(`${API_BASE}/api/v1/api-keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create API key');
  return res.json();
}

export async function revokeApiKey(keyId) {
  const res = await fetch(`${API_BASE}/api/v1/api-keys/${keyId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to revoke API key');
  return res.json();
}

export async function fetchAllocation(datasetId) {
  const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/allocation`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error('Failed to fetch allocation');
  }
  return res.json();
}

export async function runSimulatedBreach(payload) {
  const res = await fetch(`${API_BASE}/api/simulate/breach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to run simulated breach');
  return res.json();
}

export async function runMonteCarlo(payload) {
  const res = await fetch(`${API_BASE}/api/simulate/monte-carlo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to run benchmark');
  return res.json();
}

export async function testSiemWebhook(payload) {
  const res = await fetch(`${API_BASE}/api/webhooks/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to dispatch alert');
  return res.json();
}

export function getReportHtmlUrl(analysisId) {
  return `${API_BASE}/api/v1/reports/${analysisId}/html`;
}

export function getPdfReportUrl(analysisId) {
  return `${API_BASE}/api/v1/reports/${analysisId}/pdf`;
}

export function getHtmlReportUrl(analysisId) {
  return `${API_BASE}/api/v1/reports/${analysisId}/html`;
}
