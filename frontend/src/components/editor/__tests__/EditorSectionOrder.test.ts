import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EditorSectionOrder from '../EditorSectionOrder.vue'
import { useSiteBuilderStore } from '../../../stores/siteBuilderStore'

describe('EditorSectionOrder', () => {
  let store: ReturnType<typeof useSiteBuilderStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSiteBuilderStore()
    store.editableData = {
      business_name: 'Test',
      hero_headline: 'Test',
      sections: [
        { id: 'hero', type: 'hero', enabled: true, order: 0 },
        { id: 'about', type: 'about', enabled: true, order: 1 },
        { id: 'services', type: 'services', enabled: true, order: 2 },
        { id: 'faq', type: 'faq', enabled: true, order: 3 },
        { id: 'footer', type: 'footer', enabled: true, order: 4 },
      ],
    }
  })

  it('renders all sections', () => {
    const wrapper = mount(EditorSectionOrder)
    expect(wrapper.text()).toContain('Hero')
    expect(wrapper.text()).toContain('About')
    expect(wrapper.text()).toContain('Services')
    expect(wrapper.text()).toContain('FAQ')
    expect(wrapper.text()).toContain('Footer')
  })

  it('renders section labels for all types', () => {
    const wrapper = mount(EditorSectionOrder)
    // The component has SECTION_LABELS mapping
    expect(wrapper.text()).toContain('Hero')
    expect(wrapper.text()).toContain('Footer')
  })

  it('does not show delete button for pinned types (hero)', () => {
    const wrapper = mount(EditorSectionOrder)
    // Each section row has buttons. Hero and Footer should NOT have the X delete button.
    // The delete button has title="Remove section"
    const rows = wrapper.findAll('.flex.items-center.gap-2')
    // Hero is first row — should have a spacer div instead of delete button
    const heroRow = rows[0]
    expect(heroRow.find('[title="Remove section"]').exists()).toBe(false)
  })

  it('does not show delete button for pinned types (footer)', () => {
    const wrapper = mount(EditorSectionOrder)
    const rows = wrapper.findAll('.flex.items-center.gap-2')
    // Footer is last row
    const footerRow = rows[rows.length - 1]
    expect(footerRow.find('[title="Remove section"]').exists()).toBe(false)
  })

  it('shows delete button for non-pinned types', () => {
    const wrapper = mount(EditorSectionOrder)
    // There should be delete buttons in the component (one per non-pinned section)
    const deleteButtons = wrapper.findAll('[title="Remove section"]')
    // 5 sections, 2 pinned (hero, footer) = 3 delete buttons
    expect(deleteButtons.length).toBe(3)
  })

  it('has toggle switches for each section', () => {
    const wrapper = mount(EditorSectionOrder)
    // Toggle buttons have specific classes: bg-cyan-600 for enabled, bg-gray-600 for disabled
    const toggles = wrapper.findAll('.rounded-full.transition-colors')
    // Should have 5 toggles (one per section)
    expect(toggles.length).toBe(5)
  })

  it('pinned toggle switches are disabled', () => {
    const wrapper = mount(EditorSectionOrder)
    const toggles = wrapper.findAll('.rounded-full.transition-colors')
    // Hero (first) and footer (last) toggles should be disabled
    expect(toggles[0].attributes('disabled')).toBeDefined()
    expect(toggles[toggles.length - 1].attributes('disabled')).toBeDefined()
  })

  it('non-pinned toggle switches are not disabled', () => {
    const wrapper = mount(EditorSectionOrder)
    const toggles = wrapper.findAll('.rounded-full.transition-colors')
    // About (second) should not be disabled
    expect(toggles[1].attributes('disabled')).toBeUndefined()
  })

  it('has Add Section button', () => {
    const wrapper = mount(EditorSectionOrder)
    expect(wrapper.text()).toContain('Add Section')
  })

  it('has up/down move buttons', () => {
    const wrapper = mount(EditorSectionOrder)
    const moveUpButtons = wrapper.findAll('[title="Move up"]')
    const moveDownButtons = wrapper.findAll('[title="Move down"]')
    expect(moveUpButtons.length).toBe(5) // One per section
    expect(moveDownButtons.length).toBe(5)
  })

  it('first section up button is disabled', () => {
    const wrapper = mount(EditorSectionOrder)
    const moveUpButtons = wrapper.findAll('[title="Move up"]')
    expect(moveUpButtons[0].attributes('disabled')).toBeDefined()
  })

  it('last section down button is disabled', () => {
    const wrapper = mount(EditorSectionOrder)
    const moveDownButtons = wrapper.findAll('[title="Move down"]')
    expect(moveDownButtons[moveDownButtons.length - 1].attributes('disabled')).toBeDefined()
  })
})
