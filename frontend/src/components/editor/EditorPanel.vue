<template>
  <div class="w-[480px] flex-shrink-0 flex flex-col bg-gray-900 border-r border-gray-700/50 h-[calc(100vh-64px)] sticky top-[64px]">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-gray-700/50 bg-gray-900/95">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-cyan-600/20 flex items-center justify-center">
          <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </div>
        <h2 class="text-sm font-semibold text-white">Edit Site</h2>
        <span
          v-if="store.editorDirty"
          class="px-1.5 py-0.5 rounded bg-amber-600/20 border border-amber-500/30 text-amber-300 text-[10px] font-medium"
        >Unsaved</span>
        <!-- Undo/Redo -->
        <div class="flex items-center gap-0.5 ml-1">
          <button
            @click="store.undo()"
            :disabled="!store.canUndo"
            class="p-1 rounded text-gray-400 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
            title="Undo (Ctrl+Z)"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2M3 10l4-4M3 10l4 4" />
            </svg>
          </button>
          <button
            @click="store.redo()"
            :disabled="!store.canRedo"
            class="p-1 rounded text-gray-400 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
            title="Redo (Ctrl+Shift+Z)"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a5 5 0 00-5 5v2M21 10l-4-4M21 10l-4 4" />
            </svg>
          </button>
        </div>
      </div>
      <button
        @click="store.closeEditor()"
        class="text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-800"
        title="Hide editor"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- Error banner -->
    <div
      v-if="store.editorError"
      class="mx-3 mt-2 px-3 py-2 rounded-lg bg-red-900/30 border border-red-700/50 text-red-300 text-xs flex items-center justify-between"
    >
      <span>{{ store.editorError }}</span>
      <button @click="store.editorError = ''" class="text-red-400 hover:text-red-200 ml-2">&times;</button>
    </div>

    <!-- Loading state -->
    <div v-if="!store.editableData" class="flex-1 flex items-center justify-center">
      <div class="text-center space-y-2">
        <svg class="w-6 h-6 animate-spin text-cyan-400 mx-auto" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p class="text-gray-500 text-sm">Loading site data...</p>
      </div>
    </div>

    <!-- Scrollable section editors -->
    <div v-else class="flex-1 overflow-y-auto px-3 py-4 space-y-2.5 scrollbar-thin">
      <!-- Section Order Manager (replaces Visibility) -->
      <EditorSectionOrder />

      <!-- Section editors rendered in section order -->
      <template v-for="section in enabledSections" :key="section.id">
        <EditorSectionHero v-if="section.type === 'hero'" />
        <EditorSectionAbout v-if="section.type === 'about'" />
        <EditorSectionServices v-if="section.type === 'services'" @generate="openGenerate" />
        <EditorSectionGallery v-if="section.type === 'gallery'" />
        <EditorSectionCTA v-if="section.type === 'cta'" />
        <EditorSectionFAQ v-if="section.type === 'faq'" @generate="openGenerate" />
        <EditorSectionTestimonials v-if="section.type === 'testimonials'" @generate="openGenerate" />
        <EditorSectionWhyChooseUs v-if="section.type === 'why-choose-us'" @generate="openGenerate" />
        <EditorSectionHowItWorks v-if="section.type === 'how-it-works'" @generate="openGenerate" />
        <EditorSectionContact v-if="section.type === 'contact'" />
      </template>

      <!-- Always show design, social + SEO editors -->
      <EditorSectionDesign />
      <EditorSectionSocial />
      <EditorSectionSEO />
    </div>

    <!-- Action buttons -->
    <div v-if="store.editableData" class="border-t border-gray-700/50 px-4 py-3 space-y-2 bg-gray-900/95">
      <!-- Quick Preview -->
      <button
        @click="store.quickPreview()"
        class="w-full py-2 rounded-lg border border-cyan-600/50 text-cyan-300 hover:bg-cyan-600/10 text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        Quick Preview
      </button>

      <!-- Apply Changes (Full Rebuild) -->
      <button
        @click="store.applyChanges()"
        :disabled="store.isRebuilding"
        class="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-400 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2"
      >
        <svg
          v-if="store.isRebuilding"
          class="w-4 h-4 animate-spin"
          fill="none" viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ store.isRebuilding ? 'Rebuilding...' : 'Apply Changes' }}
      </button>

      <!-- Re-deploy -->
      <button
        v-if="store.resultDeployUrl"
        @click="store.redeployEditedSite()"
        :disabled="store.isRedeploying"
        class="w-full py-2 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-600/30 disabled:opacity-50 text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        <svg
          v-if="store.isRedeploying"
          class="w-4 h-4 animate-spin"
          fill="none" viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ store.isRedeploying ? 'Deploying...' : 'Re-deploy Live Site' }}
      </button>
    </div>
  </div>

  <!-- Generate Modal -->
  <GenerateModal
    :sectionType="generateSection"
    :visible="generateModalOpen"
    @close="generateModalOpen = false"
  />

  <!-- Unsaved Changes Warning -->
  <Teleport to="body">
    <div
      v-if="store.showUnsavedWarning"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="store.showUnsavedWarning = false"></div>
      <div class="relative bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6 space-y-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div>
            <h3 class="text-white font-semibold">Unsaved Changes</h3>
            <p class="text-gray-400 text-sm">You have edits that haven't been applied yet.</p>
          </div>
        </div>
        <div class="flex gap-2">
          <button
            @click="store.showUnsavedWarning = false; store.applyChanges().then(() => store.forceCloseEditor())"
            :disabled="store.isRebuilding"
            class="flex-1 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold transition-colors"
          >
            {{ store.isRebuilding ? 'Saving...' : 'Save & Close' }}
          </button>
          <button
            @click="store.forceCloseEditor()"
            class="flex-1 py-2 rounded-lg border border-gray-600 text-gray-300 hover:text-white hover:border-gray-400 text-sm font-semibold transition-colors"
          >Discard</button>
          <button
            @click="store.showUnsavedWarning = false"
            class="px-3 py-2 rounded-lg text-gray-400 hover:text-white text-sm transition-colors"
          >Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorSectionHero from './EditorSectionHero.vue'
import EditorSectionAbout from './EditorSectionAbout.vue'
import EditorSectionServices from './EditorSectionServices.vue'
import EditorSectionGallery from './EditorSectionGallery.vue'
import EditorSectionCTA from './EditorSectionCTA.vue'
import EditorSectionFAQ from './EditorSectionFAQ.vue'
import EditorSectionTestimonials from './EditorSectionTestimonials.vue'
import EditorSectionWhyChooseUs from './EditorSectionWhyChooseUs.vue'
import EditorSectionHowItWorks from './EditorSectionHowItWorks.vue'
import EditorSectionContact from './EditorSectionContact.vue'
import EditorSectionDesign from './EditorSectionDesign.vue'
import EditorSectionSEO from './EditorSectionSEO.vue'
import EditorSectionOrder from './EditorSectionOrder.vue'
import EditorSectionSocial from './EditorSectionSocial.vue'
import GenerateModal from './GenerateModal.vue'

const store = useSiteBuilderStore()
const generateModalOpen = ref(false)
const generateSection = ref('services')

const enabledSections = computed(() => {
  if (!store.editableData?.sections) return []
  return [...store.editableData.sections]
    .filter((s: any) => s.enabled)
    .sort((a: any, b: any) => a.order - b.order)
})

function openGenerate(sectionType: string) {
  generateSection.value = sectionType
  generateModalOpen.value = true
}

// Keyboard shortcuts for undo/redo
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
    e.preventDefault()
    store.undo()
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
    e.preventDefault()
    store.redo()
  }
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
</script>
