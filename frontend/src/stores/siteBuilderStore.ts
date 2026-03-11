import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import {
  generateSite, getJobStatus, getDownloadUrl, deleteDeployedSite,
  getJobEditableData, rebuildSite, generateSection, redeploySite,
} from '../services/api'
import { wsService } from '../services/websocket'

export interface PipelineStep {
  key: string
  label: string
  icon: string
}

export interface LogEntry {
  type: 'step' | 'error' | 'info'
  message: string
  timestamp: string
}

export interface GeneratedSite {
  jobId: string
  businessName: string
  title: string
  deployUrl: string | null
  deployProvider: string | null
  html: string | null
  createdAt: string
  status: 'generating' | 'completed' | 'failed'
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { key: 'parsing_url', label: 'Parse Google Maps URL', icon: '🔗' },
  { key: 'scraping_profile', label: 'Scrape Business Profile', icon: '🔍' },
  { key: 'generating_content', label: 'Generate Website Content', icon: '✍️' },
  { key: 'generating_images', label: 'Generate AI Images', icon: '🖼️' },
  { key: 'building_site', label: 'Build React Site', icon: '⚡' },
  { key: 'deploying', label: 'Deploy to Hosting', icon: '🚀' },
]

export const useSiteBuilderStore = defineStore('siteBuilder', () => {
  // ─── Core State ────────────────────────────────────────
  const phase = ref<'input' | 'progress' | 'result' | 'error'>('input')
  const mapsUrl = ref('')
  const templateName = ref('modern')
  const deployTarget = ref('auto')
  const businessContext = ref('')
  const websiteUrl = ref('')
  const isGenerating = ref(false)
  const wsConnected = ref(false)
  const currentMessage = ref('')
  const jobId = ref<string | null>(null)

  // ─── Step Tracking ─────────────────────────────────────
  const completedSteps = reactive<Set<string>>(new Set())
  const activeStep = ref<string | null>(null)
  const stepMessages = reactive<Record<string, string>>({})

  // ─── Logs ──────────────────────────────────────────────
  const logs = ref<LogEntry[]>([])

  // ─── Result ────────────────────────────────────────────
  const resultHtml = ref<string | null>(null)
  const resultTitle = ref('')
  const resultBusinessName = ref('')
  const resultDeployUrl = ref<string | null>(null)
  const resultDeployProvider = ref<string | null>(null)

  // ─── SEO Data ──────────────────────────────────────────
  const seoData = ref<Record<string, any> | null>(null)

  // ─── Error ─────────────────────────────────────────────
  const errorMessage = ref('')
  const errorDetails = ref('')

  // ─── Site History ──────────────────────────────────────
  const siteHistory = ref<GeneratedSite[]>([])

  // ─── Preview ───────────────────────────────────────────
  const previewDevice = ref<'desktop' | 'tablet' | 'mobile'>('desktop')

  // ─── Computed ──────────────────────────────────────────
  const downloadUrl = computed(() => {
    if (!jobId.value) return '#'
    return getDownloadUrl(jobId.value)
  })

  const previewWidth = computed(() => {
    switch (previewDevice.value) {
      case 'mobile': return '375px'
      case 'tablet': return '768px'
      default: return '100%'
    }
  })

  // ─── Step Helpers ──────────────────────────────────────
  function stepStatus(key: string): 'completed' | 'active' | 'pending' {
    if (completedSteps.has(key)) return 'completed'
    if (activeStep.value === key) return 'active'
    return 'pending'
  }

  function addLog(type: LogEntry['type'], message: string) {
    logs.value.push({
      type,
      message,
      timestamp: new Date().toISOString(),
    })
  }

  // ─── WebSocket Handlers ────────────────────────────────
  function handleStep(data: any) {
    const { step, status, message } = data
    if (status === 'started') {
      activeStep.value = step
      stepMessages[step] = message || ''
      addLog('step', message || `Step: ${step}`)
    } else if (status === 'progress') {
      stepMessages[step] = message || ''
      addLog('info', message || `Progress: ${step}`)
    } else if (status === 'completed') {
      completedSteps.add(step)
      if (activeStep.value === step) activeStep.value = null
      stepMessages[step] = message || 'Done'
      addLog('step', message || `Completed: ${step}`)
    } else if (status === 'error') {
      addLog('error', message || `Error in step: ${step}`)
    }
    currentMessage.value = message || currentMessage.value
  }

  function handleSiteReady(data: any) {
    const site = data.site || data
    resultTitle.value = site.title || 'Site Ready'
    resultBusinessName.value = site.business_name || 'Unknown'
    resultDeployUrl.value = site.deploy_url || null
    resultDeployProvider.value = site.deploy_provider || null
    seoData.value = site.seo || null
    if (site.job_id) {
      jobId.value = site.job_id
      fetchResult(site.job_id)
    }
  }

  function handleError(data: any) {
    errorMessage.value = data.message || 'An unknown error occurred.'
    errorDetails.value = data.details?.traceback || JSON.stringify(data.details || {}, null, 2)
    phase.value = 'error'
    isGenerating.value = false
    addLog('error', data.message || 'Error')

    // Update history
    if (jobId.value) {
      const site = siteHistory.value.find(s => s.jobId === jobId.value)
      if (site) site.status = 'failed'
    }
  }

  // ─── API Actions ───────────────────────────────────────
  async function fetchResult(id: string) {
    try {
      const job = await getJobStatus(id)
      if (job.status === 'completed' && job.result?.html) {
        resultHtml.value = job.result.html
        resultTitle.value = job.result.title || resultTitle.value
        resultBusinessName.value = job.result.business_name || resultBusinessName.value
        resultDeployUrl.value = job.result.deploy_url || resultDeployUrl.value
        resultDeployProvider.value = job.result.deploy_provider || resultDeployProvider.value
        seoData.value = job.result.seo || seoData.value
        phase.value = 'result'
        isGenerating.value = false

        // Auto-open editor when site is ready
        openEditor()

        // Update history
        const existing = siteHistory.value.find(s => s.jobId === id)
        if (existing) {
          existing.status = 'completed'
          existing.html = job.result.html
          existing.businessName = job.result.business_name || resultBusinessName.value
          existing.deployUrl = job.result.deploy_url
          existing.deployProvider = job.result.deploy_provider
          existing.title = job.result.title
        }
        saveSiteHistory()
      } else if (job.status === 'failed') {
        errorMessage.value = job.error || 'Generation failed'
        phase.value = 'error'
        isGenerating.value = false
      } else {
        setTimeout(() => fetchResult(id), 1000)
      }
    } catch (err) {
      console.error('[Store] Failed to fetch result:', err)
      errorMessage.value = 'Failed to fetch the generated site.'
      errorDetails.value = String(err)
      phase.value = 'error'
      isGenerating.value = false
    }
  }

  async function startGeneration() {
    if (!mapsUrl.value.trim() || isGenerating.value) return

    isGenerating.value = true
    phase.value = 'progress'
    completedSteps.clear()
    activeStep.value = null
    Object.keys(stepMessages).forEach(k => delete stepMessages[k])
    logs.value = []
    resultHtml.value = null
    resultTitle.value = ''
    resultBusinessName.value = ''
    resultDeployUrl.value = null
    resultDeployProvider.value = null
    errorMessage.value = ''
    errorDetails.value = ''
    currentMessage.value = 'Starting generation...'

    try {
      const response = await generateSite(
        mapsUrl.value.trim(),
        templateName.value,
        deployTarget.value,
        businessContext.value.trim(),
        websiteUrl.value.trim(),
      )
      jobId.value = response.job_id
      addLog('info', `Job created: ${response.job_id}`)

      // Add to history
      siteHistory.value.unshift({
        jobId: response.job_id,
        businessName: 'Generating...',
        title: '',
        deployUrl: null,
        deployProvider: null,
        html: null,
        createdAt: new Date().toISOString(),
        status: 'generating',
      })
      saveSiteHistory()
    } catch (err: any) {
      errorMessage.value = err.message || 'Failed to start generation.'
      phase.value = 'error'
      isGenerating.value = false
      addLog('error', `Failed to start: ${err.message}`)
    }
  }

  function resetToInput() {
    phase.value = 'input'
    isGenerating.value = false
    mapsUrl.value = ''
    businessContext.value = ''
    websiteUrl.value = ''
    completedSteps.clear()
    activeStep.value = null
    Object.keys(stepMessages).forEach(k => delete stepMessages[k])
    logs.value = []
    resultHtml.value = null
    resultTitle.value = ''
    resultBusinessName.value = ''
    resultDeployUrl.value = null
    resultDeployProvider.value = null
    seoData.value = null
    errorMessage.value = ''
    errorDetails.value = ''
    currentMessage.value = ''
    jobId.value = null
  }

  async function viewSite(site: GeneratedSite) {
    if (site.status !== 'completed') return

    // If HTML is in memory, show it directly
    if (site.html) {
      resultHtml.value = site.html
      resultTitle.value = site.title
      resultBusinessName.value = site.businessName
      resultDeployUrl.value = site.deployUrl
      resultDeployProvider.value = site.deployProvider
      jobId.value = site.jobId
      phase.value = 'result'
      return
    }

    // Otherwise fetch from backend (HTML is stripped from localStorage)
    try {
      const job = await getJobStatus(site.jobId)
      if (job.status === 'completed' && job.result?.html) {
        resultHtml.value = job.result.html
        resultTitle.value = job.result.title || site.title
        resultBusinessName.value = job.result.business_name || site.businessName
        resultDeployUrl.value = job.result.deploy_url || site.deployUrl
        resultDeployProvider.value = job.result.deploy_provider || site.deployProvider
        jobId.value = site.jobId
        phase.value = 'result'
      }
    } catch {
      // Backend doesn't have this job anymore (server restarted)
      // Can't preview without HTML — do nothing
    }
  }

  async function deleteSite(jobId: string) {
    const site = siteHistory.value.find(s => s.jobId === jobId)

    // Delete from Cloudflare/Vercel if deployed
    if (site?.deployUrl) {
      try {
        // Extract project name from URL: https://site-xxx.pages.dev -> site-xxx
        const match = site.deployUrl.match(/https?:\/\/([^.]+)\.pages\.dev/)
        if (match) {
          await deleteDeployedSite(match[1])
        }
      } catch {
        // Non-fatal — still remove from local history
      }
    }

    siteHistory.value = siteHistory.value.filter(s => s.jobId !== jobId)
    saveSiteHistory()
  }

  // ─── Persistence ───────────────────────────────────────
  function saveSiteHistory() {
    try {
      // Save without the heavy HTML content
      const lite = siteHistory.value.map(s => ({ ...s, html: null }))
      localStorage.setItem('site_builder_history', JSON.stringify(lite))
    } catch { /* ignore quota errors */ }
  }

  function loadSiteHistory() {
    try {
      const raw = localStorage.getItem('site_builder_history')
      if (raw) {
        siteHistory.value = JSON.parse(raw)
      }
    } catch { /* ignore */ }
  }

  // ─── Editor State ─────────────────────────────────────
  const editorOpen = ref(false)
  const editableData = ref<Record<string, any> | null>(null)
  const savedDataSnapshot = ref<string | null>(null) // JSON snapshot of last saved state
  const editorDirty = computed(() => {
    if (!editableData.value || !savedDataSnapshot.value) return false
    return JSON.stringify(editableData.value) !== savedDataSnapshot.value
  })
  const showUnsavedWarning = ref(false)
  const isRebuilding = ref(false)
  const isGeneratingSection = ref(false)
  const isRedeploying = ref(false)
  const editorError = ref('')
  const iframeRef = ref<HTMLIFrameElement | null>(null)

  function openEditor() {
    if (!jobId.value) return
    editorOpen.value = true
    showUnsavedWarning.value = false
    // Only fetch if we don't already have data loaded
    if (editableData.value) return
    getJobEditableData(jobId.value).then((res) => {
      editableData.value = res.data
      savedDataSnapshot.value = JSON.stringify(res.data)
    }).catch((err) => {
      console.error('[Editor] Failed to load editable data:', err)
      editorError.value = 'Failed to load site data for editing'
    })
  }

  function closeEditor() {
    if (editorDirty.value) {
      showUnsavedWarning.value = true
      return
    }
    editorOpen.value = false
  }

  function forceCloseEditor() {
    showUnsavedWarning.value = false
    editorOpen.value = false
  }

  function updateEditableField(path: string, value: any) {
    if (!editableData.value) return
    // Support dot-notation paths like "services.0.name"
    const keys = path.split('.')
    let obj: any = editableData.value
    for (let i = 0; i < keys.length - 1; i++) {
      const key = isNaN(Number(keys[i])) ? keys[i] : Number(keys[i])
      obj = obj[key]
    }
    const lastKey = isNaN(Number(keys[keys.length - 1]))
      ? keys[keys.length - 1]
      : Number(keys[keys.length - 1])
    obj[lastKey] = value
  }

  function addEditableArrayItem(path: string, item: any) {
    if (!editableData.value) return
    const arr = editableData.value[path]
    if (Array.isArray(arr)) {
      arr.push(item)
    }
  }

  function removeEditableArrayItem(path: string, index: number) {
    if (!editableData.value) return
    const arr = editableData.value[path]
    if (Array.isArray(arr)) {
      arr.splice(index, 1)
    }
  }

  function moveEditableArrayItem(path: string, from: number, direction: 'up' | 'down') {
    if (!editableData.value) return
    const arr = editableData.value[path]
    if (!Array.isArray(arr)) return
    const to = direction === 'up' ? from - 1 : from + 1
    if (to < 0 || to >= arr.length) return
    const item = arr.splice(from, 1)[0]
    arr.splice(to, 0, item)
  }

  function quickPreview() {
    if (!editableData.value || !iframeRef.value) return
    iframeRef.value.contentWindow?.postMessage(
      { type: 'QUICK_PREVIEW', payload: editableData.value },
      '*',
    )
  }

  async function applyChanges() {
    if (!jobId.value || !editableData.value) return
    isRebuilding.value = true
    editorError.value = ''
    try {
      const result = await rebuildSite(jobId.value, editableData.value)
      resultHtml.value = result.html
      // Update title/business name from edited data
      resultTitle.value = editableData.value.seo_title || resultTitle.value
      resultBusinessName.value = editableData.value.business_name || resultBusinessName.value
      // Snapshot as saved state
      savedDataSnapshot.value = JSON.stringify(editableData.value)
      showUnsavedWarning.value = false
    } catch (err: any) {
      editorError.value = err.message || 'Rebuild failed'
    } finally {
      isRebuilding.value = false
    }
  }

  async function aiGenerateSection(sectionType: string, prompt: string) {
    if (!editableData.value) return
    isGeneratingSection.value = true
    editorError.value = ''
    try {
      const result = await generateSection(sectionType, prompt, {
        business_name: editableData.value.business_name || '',
        category: editableData.value.category || '',
      })
      // Append generated items to the section array
      const arr = editableData.value[sectionType]
      if (Array.isArray(arr)) {
        arr.push(...result.items)
      } else {
        editableData.value[sectionType] = result.items
      }
      return result.items
    } catch (err: any) {
      editorError.value = err.message || 'AI generation failed'
      throw err
    } finally {
      isGeneratingSection.value = false
    }
  }

  async function redeployEditedSite() {
    if (!jobId.value) return
    isRedeploying.value = true
    editorError.value = ''
    try {
      const result = await redeploySite(jobId.value)
      resultDeployUrl.value = result.deploy_url
      resultDeployProvider.value = result.deploy_provider
    } catch (err: any) {
      editorError.value = err.message || 'Redeploy failed'
    } finally {
      isRedeploying.value = false
    }
  }

  // ─── WebSocket Lifecycle ───────────────────────────────
  function initWebSocket() {
    wsService.connect()
    wsService.on('connection_established', () => { wsConnected.value = true })
    wsService.on('step', handleStep)
    wsService.on('site_ready', handleSiteReady)
    wsService.on('error', handleError)
    wsService.on('*', () => { wsConnected.value = true })
  }

  function destroyWebSocket() {
    wsService.disconnect()
  }

  return {
    // State
    phase, mapsUrl, templateName, deployTarget, businessContext, websiteUrl, isGenerating,
    wsConnected, currentMessage, jobId,
    completedSteps, activeStep, stepMessages,
    logs, resultHtml, resultTitle, resultBusinessName,
    resultDeployUrl, resultDeployProvider, seoData,
    errorMessage, errorDetails,
    siteHistory, previewDevice,
    // Editor State
    editorOpen, editableData, savedDataSnapshot, editorDirty, showUnsavedWarning,
    isRebuilding, isGeneratingSection, isRedeploying,
    editorError, iframeRef,
    // Computed
    downloadUrl, previewWidth,
    // Actions
    stepStatus, addLog, startGeneration, resetToInput,
    viewSite, deleteSite, loadSiteHistory, saveSiteHistory,
    initWebSocket, destroyWebSocket,
    // Editor Actions
    openEditor, closeEditor, forceCloseEditor, updateEditableField,
    addEditableArrayItem, removeEditableArrayItem, moveEditableArrayItem,
    quickPreview, applyChanges, aiGenerateSection, redeployEditedSite,
  }
})
