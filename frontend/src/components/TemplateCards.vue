<template>
  <div>
    <label class="block text-sm font-medium text-gray-300 mb-3">Choose Template</label>
    <div class="grid grid-cols-3 gap-3">
      <button
        v-for="tpl in availableTemplates"
        :key="tpl.name"
        @click="$emit('select', tpl.name)"
        class="group relative rounded-xl border-2 p-3 transition-all duration-200 text-left"
        :class="selected === tpl.name
          ? 'border-cyan-500 bg-cyan-500/10 shadow-lg shadow-cyan-500/10'
          : 'border-gray-700 bg-gray-800/50 hover:border-gray-500 hover:bg-gray-800'"
      >
        <!-- Mini Preview -->
        <div
          class="w-full aspect-[4/3] rounded-lg mb-2.5 overflow-hidden"
          :class="previewClasses(tpl.name)"
        >
          <!-- Modern preview: centered layout, smooth corners -->
          <div v-if="tpl.name === 'modern'" class="h-full flex flex-col p-2">
            <div class="flex items-center gap-1 mb-1.5">
              <div class="w-3 h-3 rounded-full bg-cyan-500/60"></div>
              <div class="h-1 w-8 rounded-full bg-gray-400/30"></div>
            </div>
            <div class="flex-1 flex flex-col items-center justify-center gap-1">
              <div class="h-1.5 w-12 rounded-full bg-gray-300/50"></div>
              <div class="h-1 w-16 rounded-full bg-gray-400/30"></div>
              <div class="h-1 w-10 rounded-full bg-gray-400/20"></div>
              <div class="h-3 w-10 rounded-md bg-cyan-500/40 mt-1"></div>
            </div>
            <div class="grid grid-cols-3 gap-1 mt-auto">
              <div class="h-4 rounded bg-gray-300/20"></div>
              <div class="h-4 rounded bg-gray-300/20"></div>
              <div class="h-4 rounded bg-gray-300/20"></div>
            </div>
          </div>

          <!-- Bold preview: left-aligned, dark, dramatic -->
          <div v-else-if="tpl.name === 'bold'" class="h-full flex flex-col p-2 bg-gray-900">
            <div class="flex items-center gap-1 mb-1.5">
              <div class="w-3 h-3 bg-cyan-500/60"></div>
              <div class="h-1 w-8 bg-gray-500/30"></div>
            </div>
            <div class="flex-1 flex flex-col justify-center gap-1">
              <div class="h-2 w-14 bg-white/60"></div>
              <div class="h-1.5 w-10 bg-white/30"></div>
              <div class="h-3 w-8 bg-cyan-500/50 mt-1"></div>
            </div>
            <div class="grid grid-cols-2 gap-1 mt-auto">
              <div class="h-5 bg-gray-800 border-l-2 border-cyan-500/50"></div>
              <div class="h-5 bg-gray-800 border-l-2 border-cyan-500/50"></div>
            </div>
          </div>

          <!-- Elegant preview: minimal, warm tones, thin rules -->
          <div v-else-if="tpl.name === 'elegant'" class="h-full flex flex-col p-2 bg-stone-50">
            <div class="flex items-center justify-center gap-1 mb-1.5">
              <div class="h-[1px] w-6 bg-stone-300"></div>
            </div>
            <div class="flex-1 flex flex-col items-center justify-center gap-1">
              <div class="h-[1px] w-4 bg-stone-400/60 mb-1"></div>
              <div class="h-1.5 w-12 rounded-full bg-stone-400/40"></div>
              <div class="h-1 w-14 rounded-full bg-stone-300/30"></div>
              <div class="h-3 w-10 border border-stone-400/40 mt-1"></div>
            </div>
            <div class="grid grid-cols-3 gap-1 mt-auto">
              <div class="h-4 border-t border-stone-300/40"></div>
              <div class="h-4 border-t border-stone-300/40"></div>
              <div class="h-4 border-t border-stone-300/40"></div>
            </div>
          </div>

          <!-- Generic fallback for future templates -->
          <div v-else class="h-full flex items-center justify-center bg-gray-800 text-gray-500 text-xs">
            Preview
          </div>
        </div>

        <!-- Label -->
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-white">{{ tpl.label || tpl.name }}</h3>
            <p class="text-[11px] text-gray-500 mt-0.5 line-clamp-1">{{ tpl.description || '' }}</p>
          </div>
          <!-- Selected indicator -->
          <div
            v-if="selected === tpl.name"
            class="w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center flex-shrink-0"
          >
            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteBuilderStore } from '../stores/siteBuilderStore'

defineProps<{
  selected: string
}>()

defineEmits<{
  select: [templateName: string]
}>()

const store = useSiteBuilderStore()

const availableTemplates = computed(() =>
  store.availableTemplates.filter(t => t.available)
)

function previewClasses(name: string): string {
  switch (name) {
    case 'modern': return 'bg-gray-100'
    case 'bold': return 'bg-gray-900'
    case 'elegant': return 'bg-stone-50'
    default: return 'bg-gray-800'
  }
}
</script>
