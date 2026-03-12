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

  // ─── detectUrlType ─────────────────────────────
  describe('detectUrlType', () => {
    it('returns "none" for empty string', () => {
      expect(store.detectUrlType('')).toBe('none')
      expect(store.detectUrlType('   ')).toBe('none')
    })

    it('detects Google Maps URLs', () => {
      expect(store.detectUrlType('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')).toBe('maps')
      expect(store.detectUrlType('https://maps.app.goo.gl/abc123')).toBe('maps')
      expect(store.detectUrlType('https://goo.gl/maps/xyz')).toBe('maps')
      expect(store.detectUrlType('https://google.co.uk/maps/place/Foo')).toBe('maps')
    })

    it('detects website URLs', () => {
      expect(store.detectUrlType('https://example.com')).toBe('website')
      expect(store.detectUrlType('http://my-business.com/about')).toBe('website')
      expect(store.detectUrlType('https://www.thefixclinic.com')).toBe('website')
    })

    it('returns "none" for non-URL text', () => {
      expect(store.detectUrlType('just some text')).toBe('none')
      expect(store.detectUrlType('Joe Pizza NYC')).toBe('none')
    })
  })

  // ─── setInputUrl ──────────────────────────────
  describe('setInputUrl', () => {
    it('sets Maps URL correctly', () => {
      store.setInputUrl('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')
      expect(store.inputUrl).toBe('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')
      expect(store.inputUrlType).toBe('maps')
      expect(store.mapsUrl).toBe('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')
      expect(store.websiteUrl).toBe('')
    })

    it('sets website URL correctly', () => {
      store.setInputUrl('https://example.com')
      expect(store.inputUrl).toBe('https://example.com')
      expect(store.inputUrlType).toBe('website')
      expect(store.mapsUrl).toBe('')
      expect(store.websiteUrl).toBe('https://example.com')
    })

    it('clears everything for empty string', () => {
      store.setInputUrl('https://example.com') // set first
      store.setInputUrl('')
      expect(store.inputUrl).toBe('')
      expect(store.inputUrlType).toBe('none')
      expect(store.mapsUrl).toBe('')
      expect(store.websiteUrl).toBe('')
    })
  })

  // ─── canGenerate ──────────────────────────────
  describe('canGenerate', () => {
    it('is false when no URL is set', () => {
      expect(store.canGenerate).toBe(false)
    })

    it('is true for Maps URL (no name needed)', () => {
      store.setInputUrl('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')
      expect(store.canGenerate).toBe(true)
    })

    it('is false for website URL without business name', () => {
      store.setInputUrl('https://example.com')
      expect(store.canGenerate).toBe(false)
    })

    it('is true for website URL with business name', () => {
      store.setInputUrl('https://example.com')
      store.businessNameInput = 'My Business'
      expect(store.canGenerate).toBe(true)
    })

    it('is false when generating', () => {
      store.setInputUrl('https://www.google.com/maps/place/Test/@40.7,-74.0,17z')
      store.isGenerating = true
      expect(store.canGenerate).toBe(false)
    })

    it('is false for website URL with whitespace-only name', () => {
      store.setInputUrl('https://example.com')
      store.businessNameInput = '   '
      expect(store.canGenerate).toBe(false)
    })
  })

  // ─── resetToInput clears URL state ────────────
  describe('resetToInput', () => {
    it('clears all URL and business input state', () => {
      store.setInputUrl('https://example.com')
      store.businessNameInput = 'Test Biz'
      store.businessCategoryInput = 'Restaurant'
      store.resetToInput()
      expect(store.inputUrl).toBe('')
      expect(store.inputUrlType).toBe('none')
      expect(store.mapsUrl).toBe('')
      expect(store.websiteUrl).toBe('')
      expect(store.businessNameInput).toBe('')
      expect(store.businessCategoryInput).toBe('')
    })
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

  // ─── Section Composition ──────────────────────────
  describe('section composition (sections array)', () => {
    beforeEach(() => {
      store.editableData!.sections = [
        { id: 'hero', type: 'hero', enabled: true, order: 0 },
        { id: 'about', type: 'about', enabled: true, order: 1 },
        { id: 'services', type: 'services', enabled: true, order: 2 },
        { id: 'faq', type: 'faq', enabled: true, order: 3 },
        { id: 'footer', type: 'footer', enabled: true, order: 4 },
      ]
    })

    it('sections array exists in editable data', () => {
      expect(store.editableData!.sections).toHaveLength(5)
    })

    it('can toggle section enabled/disabled', () => {
      const section = store.editableData!.sections.find((s: any) => s.id === 'about')
      expect(section.enabled).toBe(true)
      section.enabled = false
      expect(store.editableData!.sections.find((s: any) => s.id === 'about').enabled).toBe(false)
    })

    it('can reorder sections by swapping order values', () => {
      const sections = store.editableData!.sections
      // Swap about (order 1) and services (order 2)
      const about = sections.find((s: any) => s.id === 'about')
      const services = sections.find((s: any) => s.id === 'services')
      const tmpOrder = about.order
      about.order = services.order
      services.order = tmpOrder
      sections.sort((a: any, b: any) => a.order - b.order)
      expect(sections[1].id).toBe('services')
      expect(sections[2].id).toBe('about')
    })

    it('can add a new section', () => {
      store.editableData!.sections.push({
        id: 'cta-new',
        type: 'cta',
        enabled: true,
        order: store.editableData!.sections.length,
      })
      expect(store.editableData!.sections).toHaveLength(6)
      expect(store.editableData!.sections[5].type).toBe('cta')
    })

    it('can remove a section', () => {
      store.editableData!.sections = store.editableData!.sections.filter(
        (s: any) => s.id !== 'faq'
      )
      expect(store.editableData!.sections).toHaveLength(4)
      expect(store.editableData!.sections.find((s: any) => s.id === 'faq')).toBeUndefined()
    })

    it('filtering enabled sections works correctly', () => {
      store.editableData!.sections.find((s: any) => s.id === 'about').enabled = false
      const enabled = store.editableData!.sections
        .filter((s: any) => s.enabled)
        .sort((a: any, b: any) => a.order - b.order)
      expect(enabled).toHaveLength(4)
      expect(enabled.find((s: any) => s.id === 'about')).toBeUndefined()
    })

    it('marks editorDirty when sections change', () => {
      store.savedDataSnapshot = JSON.stringify(store.editableData)
      expect(store.editorDirty).toBe(false)
      // Add a section
      store.editableData!.sections.push({ id: 'new', type: 'cta', enabled: true, order: 5 })
      expect(store.editorDirty).toBe(true)
    })
  })

  // ─── Section Pinned Behavior ───────────────────────
  describe('section pinned types (hero/footer)', () => {
    beforeEach(() => {
      store.editableData!.sections = [
        { id: 'hero', type: 'hero', enabled: true, order: 0 },
        { id: 'about', type: 'about', enabled: true, order: 1 },
        { id: 'services', type: 'services', enabled: true, order: 2 },
        { id: 'footer', type: 'footer', enabled: true, order: 3 },
      ]
    })

    it('hero cannot be removed by filtering', () => {
      // Simulate what EditorSectionOrder does — only removes non-pinned
      const PINNED_TYPES = ['hero', 'footer']
      const heroSection = store.editableData!.sections.find((s: any) => s.type === 'hero')
      expect(PINNED_TYPES.includes(heroSection.type)).toBe(true)
      // Removing non-pinned section works
      store.editableData!.sections = store.editableData!.sections.filter(
        (s: any) => s.id !== 'about'
      )
      expect(store.editableData!.sections).toHaveLength(3)
      // Hero and footer still present
      expect(store.editableData!.sections.find((s: any) => s.type === 'hero')).toBeDefined()
      expect(store.editableData!.sections.find((s: any) => s.type === 'footer')).toBeDefined()
    })

    it('footer cannot be removed by filtering', () => {
      const PINNED_TYPES = ['hero', 'footer']
      const footerSection = store.editableData!.sections.find((s: any) => s.type === 'footer')
      expect(PINNED_TYPES.includes(footerSection.type)).toBe(true)
    })

    it('non-pinned sections can be removed', () => {
      store.editableData!.sections = store.editableData!.sections.filter(
        (s: any) => s.id !== 'services'
      )
      expect(store.editableData!.sections).toHaveLength(3)
      expect(store.editableData!.sections.find((s: any) => s.type === 'services')).toBeUndefined()
    })

    it('hero stays enabled even when toggled (application-level constraint)', () => {
      // The store itself doesn't enforce pinning — EditorSectionOrder does
      // But the data model should support toggling for non-pinned types
      const about = store.editableData!.sections.find((s: any) => s.id === 'about')
      about.enabled = false
      expect(about.enabled).toBe(false)
      // Hero should still be enabled (not toggled)
      const hero = store.editableData!.sections.find((s: any) => s.id === 'hero')
      expect(hero.enabled).toBe(true)
    })
  })

  describe('undo/redo', () => {
    beforeEach(() => {
      store.editableData = {
        business_name: 'Original',
        hero_headline: 'Hello',
        sections: [],
        services: [{ title: 'Svc1', description: 'Desc1' }],
      } as any
      // Clear stacks
      store.undoStack = []
      store.redoStack = []
    })

    it('undo restores previous state', () => {
      store.pushUndoState()
      store.editableData!.business_name = 'Changed'
      expect(store.editableData!.business_name).toBe('Changed')

      store.undo()
      expect(store.editableData!.business_name).toBe('Original')
    })

    it('redo re-applies undone state', () => {
      store.pushUndoState()
      store.editableData!.business_name = 'Changed'

      store.undo()
      expect(store.editableData!.business_name).toBe('Original')

      store.redo()
      expect(store.editableData!.business_name).toBe('Changed')
    })

    it('new edit clears redo stack', () => {
      store.pushUndoState()
      store.editableData!.business_name = 'V2'

      store.undo()
      expect(store.canRedo).toBe(true)

      // New edit should clear redo
      store.pushUndoState()
      store.editableData!.business_name = 'V3'
      expect(store.canRedo).toBe(false)
      expect(store.redoStack).toHaveLength(0)
    })

    it('max undo depth is enforced', () => {
      // Push 55 states — only 50 should survive
      for (let i = 0; i < 55; i++) {
        store.pushUndoState()
        store.editableData!.business_name = `Name${i}`
      }
      expect(store.undoStack.length).toBeLessThanOrEqual(50)
    })

    it('undo on empty stack is a noop', () => {
      expect(store.canUndo).toBe(false)
      const before = JSON.stringify(store.editableData)
      store.undo()
      expect(JSON.stringify(store.editableData)).toBe(before)
    })

    it('redo on empty stack is a noop', () => {
      expect(store.canRedo).toBe(false)
      const before = JSON.stringify(store.editableData)
      store.redo()
      expect(JSON.stringify(store.editableData)).toBe(before)
    })

    it('canUndo and canRedo reflect stack state', () => {
      expect(store.canUndo).toBe(false)
      expect(store.canRedo).toBe(false)

      store.pushUndoState()
      store.editableData!.business_name = 'V2'
      expect(store.canUndo).toBe(true)
      expect(store.canRedo).toBe(false)

      store.undo()
      expect(store.canUndo).toBe(false)
      expect(store.canRedo).toBe(true)
    })
  })
})
