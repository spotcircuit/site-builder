const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9405'

export async function generateSite(
  mapsUrl: string,
  templateName: string = 'modern',
  deployTarget?: string,
  businessContext?: string,
  websiteUrl?: string,
) {
  const res = await fetch(`${API_BASE}/api/generate-site`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      maps_url: mapsUrl,
      template_name: templateName,
      deploy_target: deployTarget || null,
      business_context: businessContext || null,
      website_url: websiteUrl || null,
    })
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
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
