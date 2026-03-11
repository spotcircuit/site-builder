<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click="$emit('close')"
      ></div>

      <!-- Modal -->
      <div class="relative bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-white">AI Generate</h3>
          <button
            @click="$emit('close')"
            class="text-gray-400 hover:text-white transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Section badge -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400">Section:</span>
          <span class="px-2 py-0.5 rounded bg-purple-600/20 border border-purple-500/30 text-purple-300 text-xs font-medium">
            {{ sectionLabel }}
          </span>
        </div>

        <!-- Prompt input -->
        <div class="space-y-1">
          <label class="text-sm text-gray-300">Describe what you want</label>
          <textarea
            v-model="prompt"
            rows="3"
            class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none placeholder-gray-500"
            placeholder="e.g. Generate 4 compelling reasons why customers should choose us..."
            :disabled="isLoading"
          ></textarea>
        </div>

        <!-- Error message -->
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

        <!-- Actions -->
        <div class="flex gap-3 justify-end">
          <button
            @click="$emit('close')"
            :disabled="isLoading"
            class="px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:text-white hover:border-gray-500 text-sm transition-colors disabled:opacity-50"
          >Cancel</button>
          <button
            @click="handleGenerate"
            :disabled="isLoading || !prompt.trim()"
            class="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg
              v-if="isLoading"
              class="w-4 h-4 animate-spin"
              fill="none" viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? 'Generating...' : 'Generate' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'

const props = defineProps<{
  sectionType: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const store = useSiteBuilderStore()
const prompt = ref('')
const isLoading = ref(false)
const error = ref('')

const sectionLabel = computed(() => {
  const labels: Record<string, string> = {
    services: 'Services',
    why_choose_us: 'Why Choose Us',
    process_steps: 'How It Works',
    testimonials: 'Testimonials',
    faq_items: 'FAQ',
    gallery: 'Gallery',
  }
  return labels[props.sectionType] || props.sectionType
})

// Reset state when modal opens
watch(() => props.visible, (val) => {
  if (val) {
    prompt.value = ''
    error.value = ''
    isLoading.value = false
  }
})

async function handleGenerate() {
  if (!prompt.value.trim() || isLoading.value) return
  isLoading.value = true
  error.value = ''
  try {
    await store.aiGenerateSection(props.sectionType, prompt.value.trim())
    emit('close')
  } catch (err: any) {
    error.value = err.message || 'Generation failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
