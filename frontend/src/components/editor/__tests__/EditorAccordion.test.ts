import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EditorAccordion from '../EditorAccordion.vue'

describe('EditorAccordion', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders title', () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test Section' },
    })
    expect(wrapper.text()).toContain('Test Section')
  })

  it('renders icon when provided', () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test', icon: 'S' },
    })
    expect(wrapper.text()).toContain('S')
  })

  it('is closed by default', () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test' },
      slots: { default: '<div class="content">Inner Content</div>' },
    })
    expect(wrapper.find('.content').exists()).toBe(false)
  })

  it('opens when defaultOpen is true', () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test', defaultOpen: true },
      slots: { default: '<div class="test-content">Inner</div>' },
    })
    expect(wrapper.find('.test-content').exists()).toBe(true)
  })

  it('toggles open/closed on click', async () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test' },
      slots: { default: '<div class="test-content">Inner</div>' },
    })
    // Initially closed
    expect(wrapper.find('.test-content').exists()).toBe(false)

    // Click to open
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('.test-content').exists()).toBe(true)

    // Click to close
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('.test-content').exists()).toBe(false)
  })

  it('has chevron icon', () => {
    const wrapper = mount(EditorAccordion, {
      props: { title: 'Test' },
    })
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})
