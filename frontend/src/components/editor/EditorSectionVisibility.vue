<template>
  <EditorAccordion title="Section Visibility" icon="V">
    <div class="space-y-2">
      <div
        v-for="section in sections"
        :key="section.key"
        class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-800/50"
      >
        <span class="text-sm text-gray-300">{{ section.label }}</span>
        <button
          @click="toggleSection(section.key)"
          class="relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none"
          :class="isVisible(section.key) ? 'bg-cyan-600' : 'bg-gray-600'"
        >
          <span
            class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200"
            :class="{ 'translate-x-5': isVisible(section.key) }"
          ></span>
        </button>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()

const sections = [
  { key: 'services', label: 'Services' },
  { key: 'why_choose_us', label: 'Why Choose Us' },
  { key: 'process_steps', label: 'How It Works' },
  { key: 'testimonials', label: 'Testimonials' },
  { key: 'faq_items', label: 'FAQ' },
  { key: 'gallery', label: 'Photo Gallery' },
]

// Stores backup of hidden section data so it can be restored
const hiddenBackup: Record<string, any[]> = reactive({})

function isVisible(key: string): boolean {
  if (!store.editableData) return false
  const arr = store.editableData[key]
  return Array.isArray(arr) && arr.length > 0
}

function toggleSection(key: string) {
  if (!store.editableData) return

  if (isVisible(key)) {
    // Hide: backup current data, then clear
    hiddenBackup[key] = [...store.editableData[key]]
    store.editableData[key] = []
  } else {
    // Show: restore from backup or provide empty placeholder
    if (hiddenBackup[key] && hiddenBackup[key].length > 0) {
      store.editableData[key] = [...hiddenBackup[key]]
      delete hiddenBackup[key]
    } else {
      // No backup exists -- leave empty, user can add items via section editors
      // This means the toggle will flip back off since length is 0
      // Instead, add a single placeholder so the section is visible
      store.editableData[key] = [getPlaceholder(key)]
    }
  }
}

function getPlaceholder(key: string): any {
  switch (key) {
    case 'services':
      return { name: '', description: '', icon_suggestion: 'star' }
    case 'why_choose_us':
      return { title: '', description: '', icon_key: 'star' }
    case 'process_steps':
      return { step_number: 1, title: '', description: '', icon_key: 'circle' }
    case 'testimonials':
      return { name: '', text: '', rating: 5 }
    case 'faq_items':
      return { question: '', answer: '' }
    case 'gallery':
      return { url: '', alt: '' }
    default:
      return {}
  }
}
</script>
