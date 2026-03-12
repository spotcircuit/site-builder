const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9405'

export async function generateSite(opts: {
  mapsUrl?: string
  websiteUrl?: string
  businessName?: string
  businessCategory?: string
  templateName?: string
  deployTarget?: string
  businessContext?: string
}) {
  const res = await fetch(`${API_BASE}/api/generate-site`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      maps_url: opts.mapsUrl || null,
      template_name: opts.templateName || 'modern',
      deploy_target: opts.deployTarget || null,
      business_context: opts.businessContext || null,
      website_url: opts.websiteUrl || null,
      business_name: opts.businessName || null,
      business_category: opts.businessCategory || null,
    })
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `API error: ${res.status}`)
  }
  return res.json()
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API_BASE}/api/job/${jobId}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export function getDownloadUrl(jobId: string) {
  return `${API_BASE}/api/job/${jobId}/download`
}

export async function deleteDeployedSite(projectName: string) {
  const res = await fetch(`${API_BASE}/api/site/${projectName}`, {
    method: 'DELETE',
  })
  return res.json()
}

export function getApiBase() {
  return API_BASE
}

// ─── Image Upload ─────────────────────────────────────

export async function uploadImage(file: File): Promise<{ url: string; filename: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/api/upload-image`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `Upload failed: ${res.status}`)
  }
  const data = await res.json()
  // Convert relative URL to absolute so it works in iframe
  data.url = `${API_BASE}${data.url}`
  return data
}

// ─── Editor API ────────────────────────────────────────

export async function getJobEditableData(jobId: string) {
  const res = await fetch(`${API_BASE}/api/job/${jobId}/data`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function rebuildSite(jobId: string, data: Record<string, any>) {
  const res = await fetch(`${API_BASE}/api/rebuild-site`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, data }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `Rebuild failed: ${res.status}`)
  }
  return res.json()
}

export async function generateSection(
  sectionType: string,
  prompt: string,
  context: Record<string, any>,
) {
  const res = await fetch(`${API_BASE}/api/generate-section`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      section_type: sectionType,
      prompt,
      context,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `Generation failed: ${res.status}`)
  }
  return res.json()
}

// ─── Templates ────────────────────────────────────────

export interface TemplateInfo {
  name: string
  label?: string
  description?: string
  preview_class?: string
  available: boolean
}

export async function getTemplates(): Promise<TemplateInfo[]> {
  const res = await fetch(`${API_BASE}/api/templates`)
  if (!res.ok) return [{ name: 'modern', label: 'Modern', available: true }]
  const data = await res.json()
  return data.templates || []
}

// ─── Deploy ───────────────────────────────────────────

export async function redeploySite(jobId: string) {
  const res = await fetch(`${API_BASE}/api/redeploy-site`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `Deploy failed: ${res.status}`)
  }
  return res.json()
}
