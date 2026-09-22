/**
 * Frontend API client for DecodeX DLD-SOC Platform (/api/v1 & legacy).
 * DecodeX Security Technologies Private Limited.
 * Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.
 */

export function getApiBaseUrl() {
  if (typeof window !== 'undefined') {
    const custom = window.localStorage.getItem('decodex_api_url');
    if (custom) return custom.trim().replace(/\/+$/, '');
  }
  return (import.meta.env.VITE_API_URL || 'http://localhost:8000').trim().replace(/\/+$/, '');
}

export function setApiBaseUrl(url) {
  if (typeof window !== 'undefined') {
    if (!url) {
      window.localStorage.removeItem('decodex_api_url');
    } else {
      window.localStorage.setItem('decodex_api_url', url.trim().replace(/\/+$/, ''));
    }
  }
}

export async function checkBackendConnection() {
  const base = getApiBaseUrl();
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    const res = await fetch(`${base}/api/v1/health`, { signal: controller.signal });
    clearTimeout(timer);
    if (res.ok) {
      const data = await res.json();
      return { connected: true, data, url: base };
    }
  } catch (e) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${base}/api/health`, { signal: controller.signal });
      clearTimeout(timer);
      if (res.ok) {
        const data = await res.json();
        return { connected: true, data, url: base };
      }
    } catch (err) {
      // offline
    }
  }
  return { connected: false, url: base };
}

// Default Seed/Demo Data for Standby & Cloudflare Preview Mode
const DEMO_AGENTS = [
  { id: "AGT-ALPHA", name: "Alpha Analytics Corp", organization: "Alpha Corp", contact_email: "security@alpha-analytics.io", risk_level: "Medium", trust_score: 88.0 },
  { id: "AGT-BETA", name: "Beta Cloud Solutions", organization: "Beta Cloud LLC", contact_email: "compliance@betacloud.com", risk_level: "Low", trust_score: 94.0 },
  { id: "AGT-GAMMA", name: "Gamma AI Research Labs", organization: "Gamma AI", contact_email: "data@gamma-research.org", risk_level: "High", trust_score: 72.0 },
  { id: "AGT-DELTA", name: "Delta Growth Marketing", organization: "Delta Media", contact_email: "ops@deltagrowth.io", risk_level: "Critical", trust_score: 65.0 },
];

const DEMO_DATASETS = [
  {
    id: "DS-FINTECH-01",
    name: "Global Banking & Wealth Customer PII",
    category: "Fintech",
    description: "High-value client financial records, SSNs, credit ratings, and KYC status.",
    total_records: 100,
    columns: ["id", "customer_name", "email", "ssn", "credit_score", "account_balance", "account_tier"],
    created_at: "2026-09-20T10:00:00Z"
  },
  {
    id: "DS-HEALTH-02",
    name: "Clinical Patient Treatment & EHR Records",
    category: "Healthcare",
    description: "Confidential HIPAA-regulated electronic health records and diagnosis histories.",
    total_records: 80,
    columns: ["id", "patient_name", "email", "diagnosis", "treating_physician", "insurance_provider"],
    created_at: "2026-09-21T14:30:00Z"
  }
];

const DEMO_ALLOCATION = {
  allocation_id: "ALLOC-DEMO-99",
  dataset_id: "DS-FINTECH-01",
  strategy_used: "overlap_minimization",
  canary_injection_rate: 0.04,
  total_unique_records_allocated: 100,
  average_pairwise_overlap: 0.22,
  total_canaries_injected: 4,
  allocations: {
    "AGT-ALPHA": { agent_id: "AGT-ALPHA", agent_name: "Alpha Analytics Corp", total_records: 65, genuine_records_count: 62, canary_records_count: 3, canary_tokens: ["CNY-ALP-01", "CNY-ALP-02", "CNY-ALP-03"], download_url: "#" },
    "AGT-BETA": { agent_id: "AGT-BETA", agent_name: "Beta Cloud Solutions", total_records: 65, genuine_records_count: 63, canary_records_count: 2, canary_tokens: ["CNY-BET-01", "CNY-BET-02"], download_url: "#" },
    "AGT-GAMMA": { agent_id: "AGT-GAMMA", agent_name: "Gamma AI Research Labs", total_records: 65, genuine_records_count: 61, canary_records_count: 4, canary_tokens: ["CNY-GAM-01", "CNY-GAM-02", "CNY-GAM-03", "CNY-GAM-04"], download_url: "#" },
    "AGT-DELTA": { agent_id: "AGT-DELTA", agent_name: "Delta Growth Marketing", total_records: 65, genuine_records_count: 61, canary_records_count: 4, canary_tokens: ["CNY-DEL-01", "CNY-DEL-02", "CNY-DEL-03", "CNY-DEL-04"], download_url: "#" },
  },
  overlap_matrix: {
    "AGT-ALPHA": { "AGT-ALPHA": 1.0, "AGT-BETA": 0.24, "AGT-GAMMA": 0.21, "AGT-DELTA": 0.20 },
    "AGT-BETA": { "AGT-ALPHA": 0.24, "AGT-BETA": 1.0, "AGT-GAMMA": 0.23, "AGT-DELTA": 0.22 },
    "AGT-GAMMA": { "AGT-ALPHA": 0.21, "AGT-BETA": 0.23, "AGT-GAMMA": 1.0, "AGT-DELTA": 0.21 },
    "AGT-DELTA": { "AGT-ALPHA": 0.20, "AGT-BETA": 0.22, "AGT-GAMMA": 0.21, "AGT-DELTA": 1.0 }
  },
  created_at: "2026-09-22T08:00:00Z"
};

export async function fetchHealth() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/health`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    status: 'healthy',
    mode: 'standby_demo',
    service: 'DecodeX Data Leakage Detection & Cyber Attribution Platform',
    version: '2.1.0',
    owning_organization: 'DecodeX Security Technologies Private Limited',
    integration_target: 'DecodeX Threat Hunting SOC (Standby Demo)'
  };
}

export async function fetchDatasets() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/datasets`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return DEMO_DATASETS;
}

export async function fetchDatasetDetails(id) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/datasets/${id}`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const found = DEMO_DATASETS.find(d => d.id === id) || DEMO_DATASETS[0];
  return {
    ...found,
    sample_records: [
      { id: "REC-FIN-0001", customer_name: "Eleanor Vance", email: "eleanor.vance@example.com", ssn: "***-**-4912", credit_score: 780, account_balance: 48920.50, account_tier: "Platinum" },
      { id: "REC-FIN-0002", customer_name: "Marcus Holloway", email: "marcus.h@example.com", ssn: "***-**-8120", credit_score: 715, account_balance: 14200.00, account_tier: "Gold" },
      { id: "REC-FIN-0003", customer_name: "Sophia Chen", email: "schen@example.com", ssn: "***-**-3349", credit_score: 820, account_balance: 112450.75, account_tier: "Platinum" }
    ]
  };
}

export async function generateDataset(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/datasets/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const newDs = {
    id: `DS-${payload.category ? payload.category.toUpperCase().slice(0, 4) : 'GEN'}-${Math.floor(1000 + Math.random() * 9000)}`,
    name: payload.name,
    category: payload.category || 'Fintech',
    description: `Generated synthetic ${payload.category} dataset with ${payload.num_records} records.`,
    total_records: Number(payload.num_records) || 100,
    columns: ["id", "customer_name", "email", "ssn", "credit_score", "account_balance"],
    created_at: new Date().toISOString()
  };
  DEMO_DATASETS.unshift(newDs);
  return newDs;
}

export async function uploadDataset(formData) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/datasets/upload`, {
      method: 'POST',
      body: formData
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const name = formData.get('name') || 'Uploaded Enterprise Dataset';
  const category = formData.get('category') || 'Fintech';
  const newDs = {
    id: `DS-UPL-${Math.floor(1000 + Math.random() * 9000)}`,
    name,
    category,
    description: `Uploaded ${category} dataset.`,
    total_records: 120,
    columns: ["id", "customer_name", "email", "ssn", "credit_score", "account_balance"],
    created_at: new Date().toISOString()
  };
  DEMO_DATASETS.unshift(newDs);
  return newDs;
}

export async function fetchAgents() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/agents`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return DEMO_AGENTS;
}

export async function createAgent(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const newAgent = {
    id: `AGT-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
    ...payload,
    is_active: true
  };
  DEMO_AGENTS.push(newAgent);
  return newAgent;
}

export async function updateAgent(id, payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const idx = DEMO_AGENTS.findIndex(a => a.id === id);
  if (idx !== -1) {
    DEMO_AGENTS[idx] = { ...DEMO_AGENTS[idx], ...payload };
    return DEMO_AGENTS[idx];
  }
  return payload;
}

export async function deleteAgent(id) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/agents/${id}`, {
      method: 'DELETE'
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  const idx = DEMO_AGENTS.findIndex(a => a.id === id);
  if (idx !== -1) DEMO_AGENTS.splice(idx, 1);
  return { success: true };
}

export async function createAllocation(config) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/distribute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    ...DEMO_ALLOCATION,
    dataset_id: config.dataset_id,
    canary_injection_rate: config.canary_injection_rate || 0.04
  };
}

export function getDownloadUrl(allocationId, agentId) {
  const base = getApiBaseUrl();
  return `${base}/api/v1/distribute/${allocationId}/agent/${agentId}/download`;
}

export async function analyzeLeakedFile(formData) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/analyze/file`, {
      method: 'POST',
      body: formData
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  // Simulated fallback analysis
  return generateDemoAnalysisResult("Delta Growth Marketing", "AGT-DELTA", 2);
}

export async function analyzeLeakedJson(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return generateDemoAnalysisResult("Beta Cloud Solutions", "AGT-BETA", 1);
}

export async function fetchEvents(params = {}) {
  const base = getApiBaseUrl();
  try {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${base}/api/v1/events?${query}`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return [
    {
      event_id: "evt_7a42b109",
      event_type: "guilt_detection",
      severity: "critical",
      confidence_score: 0.998,
      source_dataset: "Global Banking & Wealth Customer PII",
      implicated_agent: "Delta Growth Marketing (AGT-DELTA)",
      evidence: { canary_hits: 2, matched_records: 48, leak_source: "Dark Web Forum Paste" },
      timestamp: new Date(Date.now() - 3600000).toISOString()
    },
    {
      event_id: "evt_3c89f214",
      event_type: "canary_tripped",
      severity: "critical",
      confidence_score: 1.0,
      source_dataset: "Global Banking & Wealth Customer PII",
      implicated_agent: "Delta Growth Marketing (AGT-DELTA)",
      evidence: { canary_token: "CNY-DEL-02", record_hash: "CANARY-4f9e1a" },
      timestamp: new Date(Date.now() - 3600000).toISOString()
    },
    {
      event_id: "evt_1a90c482",
      event_type: "allocation_created",
      severity: "info",
      confidence_score: 1.0,
      source_dataset: "Global Banking & Wealth Customer PII",
      implicated_agent: "All Authorized Vendors",
      evidence: { strategy: "overlap_minimization", canary_rate: 0.04, total_agents: 4 },
      timestamp: new Date(Date.now() - 86400000).toISOString()
    }
  ];
}

export async function fetchIntegrationSettings() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/integrations`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    id: "cfg_decodex_default",
    target_name: "DecodeX Threat Hunting Platform",
    endpoint_url: "http://localhost:8001/api/v1/alerts",
    api_key: "",
    is_enabled: true,
    alert_on_guilt: true,
    alert_on_canary: true,
    min_confidence_threshold: "0.75"
  };
}

export async function updateIntegrationSettings(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/integrations`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return { id: "cfg_decodex_default", ...payload };
}

export async function testSocConnection() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/integrations/test`, { method: 'POST' });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    success: true,
    status_code: 200,
    details: { ping: true, simulation: true },
    message: "Connected successfully to DecodeX SOC (Simulation Standby Mode)"
  };
}

export async function fetchApiKeys() {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/api-keys`);
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return [
    {
      id: "key_decodex_soc_service",
      name: "DecodeX Threat Hunting Platform Service Account",
      prefix: "dld_live_9a",
      scopes: ["events:read", "alerts:write"],
      is_active: true,
      last_used_at: new Date().toISOString(),
      created_at: "2026-09-01T00:00:00Z"
    }
  ];
}

export async function createApiKey(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/api-keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    id: `key_${Math.random().toString(36).substring(2, 10)}`,
    name: payload.name,
    raw_key: `dld_live_${Math.random().toString(36).substring(2, 18)}_${Math.random().toString(36).substring(2, 18)}`,
    prefix: "dld_live_xx",
    scopes: payload.scopes || ["events:read"],
    is_active: true,
    created_at: new Date().toISOString()
  };
}

export async function revokeApiKey(keyId) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/v1/api-keys/${keyId}`, { method: 'DELETE' });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return { success: true };
}

export async function fetchAllocation(datasetId) {
  const base = getApiBaseUrl();
  try {
    // Try primary route
    const res = await fetch(`${base}/api/datasets/${datasetId}/allocation`);
    if (res.ok) return await res.json();
    // Try v1 route
    const resV1 = await fetch(`${base}/api/v1/distribute/dataset/${datasetId}`);
    if (resV1.ok) return await resV1.json();
  } catch (e) {
    // fallback
  }
  return { ...DEMO_ALLOCATION, dataset_id: datasetId };
}

export async function runSimulatedBreach(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/simulate/breach`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }

  // Standby / Client-side simulation fallback for Cloudflare Pages preview
  const targetId = payload.target_agent_id || "AGT-DELTA";
  const agent = DEMO_AGENTS.find(a => a.id === targetId) || DEMO_AGENTS[3];
  const canaryTriggered = Math.random() > 0.2;
  const analysisResult = generateDemoAnalysisResult(agent.name, agent.id, canaryTriggered ? 2 : 0);

  return {
    scenario_title: `Adversarial Exfiltration Leak from Agent ${agent.name} (${agent.id})`,
    actual_culprit_ids: [agent.id],
    total_simulated_leaked_records: Math.floor(40 + Math.random() * 30),
    attribution_success: true,
    canary_triggered: canaryTriggered,
    analysis_result: analysisResult
  };
}

export async function runMonteCarlo(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/simulate/monte-carlo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        iterations: Math.max(10, payload.iterations || 20)
      })
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }

  return {
    dataset_id: payload.dataset_id,
    total_iterations_per_rate: payload.iterations || 30,
    leak_percentage_tested: payload.leak_percentage || 0.5,
    benchmarks: [
      { canary_rate_pct: 0, total_simulations: 30, accuracy_percentage: 86.7, canary_direct_hit_percentage: 0.0, avg_detection_confidence: 88.2 },
      { canary_rate_pct: 2, total_simulations: 30, accuracy_percentage: 93.3, canary_direct_hit_percentage: 73.3, avg_detection_confidence: 96.0 },
      { canary_rate_pct: 5, total_simulations: 30, accuracy_percentage: 100.0, canary_direct_hit_percentage: 96.7, avg_detection_confidence: 100.0 },
      { canary_rate_pct: 10, total_simulations: 30, accuracy_percentage: 100.0, canary_direct_hit_percentage: 100.0, avg_detection_confidence: 100.0 }
    ]
  };
}

export async function testSiemWebhook(payload) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}/api/webhooks/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch (e) {
    // fallback
  }
  return {
    status: "dispatched",
    target_siem: payload.siem_type || "Splunk",
    analysis_id: payload.analysis_id,
    event_type: "DATA_LEAKAGE_ATTRIBUTION_ALERT",
    timestamp: new Date().toISOString(),
    payload_preview: {
      alert_id: `alert_${Math.random().toString(36).substring(2, 10)}`,
      severity: "CRITICAL",
      confidence_score: 1.0,
      owning_organization: "DecodeX Security Technologies Private Limited"
    }
  };
}

export function getReportHtmlUrl(analysisId) {
  const base = getApiBaseUrl();
  return `${base}/api/v1/reports/${analysisId}/html`;
}

export function getPdfReportUrl(analysisId) {
  const base = getApiBaseUrl();
  return `${base}/api/v1/reports/${analysisId}/pdf`;
}

export function getHtmlReportUrl(analysisId) {
  const base = getApiBaseUrl();
  return `${base}/api/v1/reports/${analysisId}/html`;
}

function generateDemoAnalysisResult(targetName, targetId, canaryHits) {
  const analysisId = `LEAK-ANL-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  const isCanary = canaryHits > 0;
  
  const scores = DEMO_AGENTS.map(a => {
    const isTarget = a.id === targetId;
    const prob = isTarget ? (isCanary ? 1.0 : 0.982) : (Math.random() * 0.15);
    return {
      agent_id: a.id,
      agent_name: a.name,
      guilt_probability: Number(prob.toFixed(4)),
      matching_records_count: isTarget ? 48 : Math.floor(10 + Math.random() * 12),
      matching_genuine_count: isTarget ? 46 : Math.floor(10 + Math.random() * 12),
      canary_records_found: isTarget ? canaryHits : 0,
      triggered_canary_tokens: isTarget && canaryHits > 0 ? [`CNY-${targetId.replace('AGT-', '')}-01`, `CNY-${targetId.replace('AGT-', '')}-02`] : [],
      verdict: isTarget ? (isCanary ? "CONFIRMED_LEAKER" : "PRIMARY_SUSPECT") : "CLEARED",
      explanation: isTarget 
        ? (isCanary ? `Cryptographic Honeytoken match verified (${canaryHits} canaries tripped). Mathematical certainty: 100%.` : `High probabilistic match (${(prob * 100).toFixed(1)}%) based on minimal overlap distribution.`)
        : "Guilt probability below enterprise alert threshold."
    };
  }).sort((a, b) => b.guilt_probability - a.guilt_probability);

  return {
    analysis_id: analysisId,
    dataset_id: "DS-FINTECH-01",
    leak_source_name: "Dark Web Forum Paste",
    total_leaked_records: 52,
    matched_leaked_records: 48,
    unmatched_leaked_records: 4,
    canary_hits_total: canaryHits,
    independent_leak_prob_p: 0.05,
    top_suspect_id: targetId,
    top_suspect_name: targetName,
    highest_probability: isCanary ? 1.0 : 0.982,
    canary_confirmed_agent_id: isCanary ? targetId : null,
    agent_scores: scores,
    overlap_matrix: DEMO_ALLOCATION.overlap_matrix,
    analyzed_at: new Date().toISOString()
  };
}
