import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'

describe('siteBuilderStore - Editor', () => {
  let store: ReturnType<typeof useSiteBuilderStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSiteBuilderStore()
    // Set up editable data directly
    store.editableData = {
      business_name: 'Test Business',
      hero_headline: 'Welcome',
      services: [
        { name: 'Service A', description: 'Desc A' },
        { name: 'Service B', description: 'Desc B' },
        { name: 'Service C', description: 'Desc C' },
      ],
      faq_items: [
        { question: 'Q1', answer: 'A1' },
        { question: 'Q2', answer: 'A2' },
      ],
      testimonials: [
        { author: 'Alice', rating: 5, text: 'Great!' },
      ],
      why_choose_us: [
        { title: 'Fast', description: 'Quick service', icon_key: 'clock' },
      ],
      process_steps: [
        { step_number: 1, title: 'Step 1', description: 'First step' },
        { step_number: 2, title: 'Step 2', description: 'Second step' },
      ],
    }
  })

  // ─── updateEditableField ─────────────────────────
  describe('updateEditableField', () => {
    it('updates a top-level field', () => {
      store.updateEditableField('hero_headline', 'New Headline')
      expect(store.editableData?.hero_headline).toBe('New Headline')
    })

    it('updates a nested field via dot notation', () => {
      store.updateEditableField('services.0.name', 'Plumbing')
      expect(store.editableData?.services[0].name).toBe('Plumbing')
    })

    it('updates the last item in array', () => {
      store.updateEditableField('services.2.description', 'Updated C')
      expect(store.editableData?.services[2].description).toBe('Updated C')
    })

    it('does nothing if editableData is null', () => {
      store.editableData = null
      store.updateEditableField('hero_headline', 'test')
      expect(store.editableData).toBeNull()
    })
  })

  // ─── addEditableArrayItem ────────────────────────
  describe('addEditableArrayItem', () => {
    it('adds an item to services', () => {
      store.addEditableArrayItem('services', { name: 'New', description: 'New desc' })
      expect(store.editableData?.services).toHaveLength(4)
      expect(store.editableData?.services[3].name).toBe('New')
    })

    it('adds an item to faq_items', () => {
      store.addEditableArrayItem('faq_items', { question: 'Q3', answer: 'A3' })
      expect(store.editableData?.faq_items).toHaveLength(3)
    })

    it('does nothing if path is not an array', () => {
      store.addEditableArrayItem('hero_headline', { name: 'x' })
      expect(store.editableData?.hero_headline).toBe('Welcome')
    })

    it('does nothing if editableData is null', () => {
      store.editableData = null
      store.addEditableArrayItem('services', { name: 'x' })
      expect(store.editableData).toBeNull()
    })
  })

  // ─── removeEditableArrayItem ─────────────────────
  describe('removeEditableArrayItem', () => {
    it('removes an item by index', () => {
      store.removeEditableArrayItem('services', 1)
      expect(store.editableData?.services).toHaveLength(2)
      expect(store.editableData?.services[0].name).toBe('Service A')
      expect(store.editableData?.services[1].name).toBe('Service C')
    })

    it('removes the first item', () => {
      store.removeEditableArrayItem('services', 0)
      expect(store.editableData?.services).toHaveLength(2)
      expect(store.editableData?.services[0].name).toBe('Service B')
    })

    it('removes the last item', () => {
      store.removeEditableArrayItem('services', 2)
      expect(store.editableData?.services).toHaveLength(2)
    })

    it('does nothing if editableData is null', () => {
      store.editableData = null
      store.removeEditableArrayItem('services', 0)
      expect(store.editableData).toBeNull()
    })
  })

  // ─── moveEditableArrayItem ───────────────────────
  describe('moveEditableArrayItem', () => {
    it('moves an item up', () => {
      store.moveEditableArrayItem('services', 1, 'up')
      expect(store.editableData?.services[0].name).toBe('Service B')
      expect(store.editableData?.services[1].name).toBe('Service A')
      expect(store.editableData?.services[2].name).toBe('Service C')
    })

    it('moves an item down', () => {
      store.moveEditableArrayItem('services', 0, 'down')
      expect(store.editableData?.services[0].name).toBe('Service B')
      expect(store.editableData?.services[1].name).toBe('Service A')
    })

    it('does not move first item up (boundary)', () => {
      store.moveEditableArrayItem('services', 0, 'up')
      expect(store.editableData?.services[0].name).toBe('Service A')
    })

    it('does not move last item down (boundary)', () => {
      store.moveEditableArrayItem('services', 2, 'down')
      expect(store.editableData?.services[2].name).toBe('Service C')
    })

    it('does nothing for non-array path', () => {
      store.moveEditableArrayItem('hero_headline', 0, 'up')
      expect(store.editableData?.hero_headline).toBe('Welcome')
    })

    it('does nothing if editableData is null', () => {
      store.editableData = null
      store.moveEditableArrayItem('services', 0, 'up')
      expect(store.editableData).toBeNull()
    })
  })

  // ─── Dirty Tracking ─────────────────────────────
  describe('editorDirty', () => {
    it('is false when no snapshot exists', () => {
      expect(store.editorDirty).toBe(false)
    })

    it('is false when data matches snapshot', () => {
      store.savedDataSnapshot = JSON.stringify(store.editableData)
      expect(store.editorDirty).toBe(false)
    })

    it('is true when data differs from snapshot', () => {
      store.savedDataSnapshot = JSON.stringify(store.editableData)
      store.updateEditableField('hero_headline', 'Changed!')
      expect(store.editorDirty).toBe(true)
    })
  })

  // ─── Close Editor ────────────────────────────────
  describe('closeEditor', () => {
    it('closes when not dirty', () => {
      store.editorOpen = true
      store.closeEditor()
      expect(store.editorOpen).toBe(false)
    })

    it('shows unsaved warning when dirty', () => {
      store.editorOpen = true
      // Make it dirty by setting snapshot then changing data
      store.savedDataSnapshot = JSON.stringify(store.editableData)
      store.updateEditableField('hero_headline', 'Changed!')
      store.closeEditor()
      // Should NOT close, should show warning
      expect(store.showUnsavedWarning).toBe(true)
      expect(store.editorOpen).toBe(true)
    })
  })

  // ─── Force Close Editor ──────────────────────────
  describe('forceCloseEditor', () => {
    it('closes editor regardless of dirty state', () => {
      store.editorOpen = true
      store.showUnsavedWarning = true
      store.forceCloseEditor()
      expect(store.editorOpen).toBe(false)
      expect(store.showUnsavedWarning).toBe(false)
    })
  })
})
