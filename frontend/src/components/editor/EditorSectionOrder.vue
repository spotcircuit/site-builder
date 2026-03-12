<template>
  <EditorAccordion title="Section Order" icon="O" defaultOpen>
    <div class="space-y-1.5">
      <div
        v-for="(section, index) in orderedSections"
        :key="section.id"
        class="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
        :class="section.enabled ? 'bg-gray-800/50' : 'bg-gray-800/20 opacity-60'"
      >
        <!-- Reorder arrows -->
        <div class="flex flex-col gap-0.5">
          <button
            @click="moveSection(index, 'up')"
            :disabled="index === 0"
            class="p-0.5 text-gray-500 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
            title="Move up"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <button
            @click="moveSection(index, 'down')"
            :disabled="index === orderedSections.length - 1"
            class="p-0.5 text-gray-500 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
            title="Move down"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        <!-- Section name -->
        <span class="flex-1 text-sm text-gray-300">{{ sectionLabel(section.type) }}</span>

        <!-- Toggle switch -->
        <button
          @click="toggleSection(section.id)"
          :disabled="isPinned(section.type)"
          class="relative w-9 h-5 rounded-full transition-colors duration-200 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
          :class="section.enabled ? 'bg-cyan-600' : 'bg-gray-600'"
        >
          <span
            class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200"
            :class="{ 'translate-x-4': section.enabled }"
          ></span>
        </button>

        <!-- Delete button -->
        <button
          v-if="!isPinned(section.type)"
          @click="removeSection(section.id)"
          class="p-1 text-red-400/40 hover:text-red-400 transition-colors rounded hover:bg-gray-700"
          title="Remove section"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div v-else class="w-[22px]"></div>
      </div>
    </div>

    <!-- Add Section -->
    <div class="mt-3 relative" ref="addMenuRef">
      <button
        @click="showAddMenu = !showAddMenu"
        class="w-full py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors flex items-center justify-center gap-1"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Add Section
      </button>

      <!-- Dropdown menu -->
      <div
        v-if="showAddMenu"
        class="absolute bottom-full left-0 right-0 mb-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-10 max-h-48 overflow-y-auto"
      >
        <button
          v-for="type in addableSectionTypes"
          :key="type"
          @click="addSection(type)"
          class="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors first:rounded-t-lg last:rounded-b-lg"
        >
          {{ sectionLabel(type) }}
        </button>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()
const showAddMenu = ref(false)
const addMenuRef = ref<HTMLElement | null>(null)

// Section type labels for display
const SECTION_LABELS: Record<string, string> = {
  'hero': 'Hero',
  'social-proof': 'Social Proof',
  'about': 'About',
  'services': 'Services',
  'why-choose-us': 'Why Choose Us',
  'how-it-works': 'How It Works',
  'gallery': 'Gallery',
  'testimonials': 'Testimonials',
  'faq': 'FAQ',
  'cta': 'Call to Action',
  'contact': 'Contact',
  'footer': 'Footer',
}

// Pinned sections that can't be deleted or disabled
const PINNED_TYPES = ['hero', 'footer']

// All available section types for the add menu
const ALL_SECTION_TYPES = [
  'hero', 'social-proof', 'about', 'services', 'why-choose-us',
  'how-it-works', 'gallery', 'testimonials', 'faq', 'cta', 'contact', 'footer'
]

function sectionLabel(type: string): string {
  return SECTION_LABELS[type] || type
}

function isPinned(type: string): boolean {
  return PINNED_TYPES.includes(type)
}

const orderedSections = computed(() => {
  if (!store.editableData?.sections) return []
  return [...store.editableData.sections].sort((a: any, b: any) => a.order - b.order)
})

// Section types that can be added (allow duplicates for CTA)
const addableSectionTypes = computed(() => {
  return ALL_SECTION_TYPES
})

function moveSection(fromIndex: number, direction: 'up' | 'down') {
  if (!store.editableData?.sections) return
  const sections = store.editableData.sections
  // Sort by order to get current visual order
  sections.sort((a: any, b: any) => a.order - b.order)
  const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1
  if (toIndex < 0 || toIndex >= sections.length) return
  // Swap orders
  const temp = sections[fromIndex].order
  sections[fromIndex].order = sections[toIndex].order
  sections[toIndex].order = temp
  // Re-sort
  sections.sort((a: any, b: any) => a.order - b.order)
  // Normalize order values
  sections.forEach((s: any, i: number) => s.order = i)
}

function toggleSection(sectionId: string) {
  if (!store.editableData?.sections) return
  const section = store.editableData.sections.find((s: any) => s.id === sectionId)
  if (section && !isPinned(section.type)) {
    section.enabled = !section.enabled
  }
}

function removeSection(sectionId: string) {
  if (!store.editableData?.sections) return
  const section = store.editableData.sections.find((s: any) => s.id === sectionId)
  if (section && isPinned(section.type)) return
  store.editableData.sections = store.editableData.sections.filter(
    (s: any) => s.id !== sectionId
  )
  // Renormalize order
  store.editableData.sections.sort((a: any, b: any) => a.order - b.order)
  store.editableData.sections.forEach((s: any, i: number) => s.order = i)
}

function addSection(type: string) {
  if (!store.editableData?.sections) return
  const newId = `${type}-${Date.now()}`
  store.editableData.sections.push({
    id: newId,
    type,
    enabled: true,
    order: store.editableData.sections.length,
  })
  showAddMenu.value = false
}

// Close add menu on click outside
function handleClickOutside(e: MouseEvent) {
  if (addMenuRef.value && !addMenuRef.value.contains(e.target as Node)) {
    showAddMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
