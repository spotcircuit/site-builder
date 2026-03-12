import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TemplateCards from '../TemplateCards.vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'

describe('TemplateCards', () => {
  let store: ReturnType<typeof useSiteBuilderStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSiteBuilderStore()
    // Provide available templates
    store.availableTemplates = [
      { name: 'modern', label: 'Modern', description: 'Clean and professional', available: true },
      { name: 'bold', label: 'Bold', description: 'Dramatic and high-contrast', available: true },
      { name: 'elegant', label: 'Elegant', description: 'Refined and minimal', available: true },
    ]
  })

  it('renders all available templates', () => {
    const wrapper = mount(TemplateCards, {
      props: { selected: 'modern' },
    })
    expect(wrapper.text()).toContain('Modern')
    expect(wrapper.text()).toContain('Bold')
    expect(wrapper.text()).toContain('Elegant')
  })

  it('emits select event with template name on click', async () => {
    const wrapper = mount(TemplateCards, {
      props: { selected: 'modern' },
    })
    const buttons = wrapper.findAll('button')
    // Click the "Bold" button (second one)
    await buttons[1].trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual(['bold'])
  })

  it('highlights selected template with cyan border', () => {
    const wrapper = mount(TemplateCards, {
      props: { selected: 'modern' },
    })
    const buttons = wrapper.findAll('button')
    // First button (modern) should have cyan border class
    expect(buttons[0].classes()).toContain('border-cyan-500')
    // Second button (bold) should not
    expect(buttons[1].classes()).not.toContain('border-cyan-500')
  })

  it('shows checkmark on selected template', () => {
    const wrapper = mount(TemplateCards, {
      props: { selected: 'elegant' },
    })
    const buttons = wrapper.findAll('button')
    // Elegant is 3rd — should have the checkmark SVG visible
    const elegantBtn = buttons[2]
    expect(elegantBtn.find('.bg-cyan-500').exists()).toBe(true)
    // Modern (1st) should NOT have checkmark
    expect(buttons[0].find('.bg-cyan-500').exists()).toBe(false)
  })

  it('filters out unavailable templates', () => {
    store.availableTemplates = [
      { name: 'modern', label: 'Modern', description: '', available: true },
      { name: 'bold', label: 'Bold', description: '', available: false },
      { name: 'elegant', label: 'Elegant', description: '', available: true },
    ]
    const wrapper = mount(TemplateCards, {
      props: { selected: 'modern' },
    })
    expect(wrapper.text()).toContain('Modern')
    expect(wrapper.text()).not.toContain('Bold')
    expect(wrapper.text()).toContain('Elegant')
  })

  it('renders template descriptions', () => {
    const wrapper = mount(TemplateCards, {
      props: { selected: 'modern' },
    })
    expect(wrapper.text()).toContain('Clean and professional')
    expect(wrapper.text()).toContain('Dramatic and high-contrast')
  })
})
