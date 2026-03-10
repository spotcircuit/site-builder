<template>
  <section class="space-y-6">
    <div class="text-center mb-6">
      <h2 class="text-2xl font-bold text-white mb-1">Building Your Site</h2>
      <p class="text-gray-400">{{ store.currentMessage || 'Starting...' }}</p>
    </div>

    <!-- Progress Bar -->
    <div class="bg-gray-800/50 rounded-full h-2 overflow-hidden">
      <div
        class="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-700 ease-out"
        :style="{ width: progressPercent + '%' }"
      ></div>
    </div>

    <!-- Step Indicators -->
    <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6">
      <div class="space-y-4">
        <div
          v-for="s in steps"
          :key="s.key"
          class="flex items-center gap-4 transition-all duration-300"
          :class="{ 'opacity-40': store.stepStatus(s.key) === 'pending' }"
        >
          <div
            class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 text-sm"
            :class="stepIconClass(s.key)"
          >
            <svg
              v-if="store.stepStatus(s.key) === 'completed'"
              class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
            <svg
              v-else-if="store.stepStatus(s.key) === 'active'"
              class="animate-spin w-4 h-4 text-cyan-400" viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            <span v-else>{{ s.icon }}</span>
          </div>

          <div class="flex-1 min-w-0">
            <p
              class="font-medium transition-colors duration-300"
              :class="{
                'text-white': store.stepStatus(s.key) === 'active',
                'text-cyan-400': store.stepStatus(s.key) === 'completed',
                'text-gray-500': store.stepStatus(s.key) === 'pending',
              }"
            >
              {{ s.label }}
            </p>
            <p
              v-if="store.stepMessages[s.key]"
              class="text-sm text-gray-400 mt-0.5 truncate"
            >
              {{ store.stepMessages[s.key] }}
            </p>
          </div>

          <span
            v-if="store.stepStatus(s.key) === 'completed'"
            class="text-xs text-cyan-500 font-medium flex-shrink-0"
          >Done</span>
        </div>
      </div>
    </div>

    <!-- Live Log (collapsible) -->
    <details class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
      <summary class="px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none">
        Live Log ({{ store.logs.length }} entries)
      </summary>
      <div class="px-4 pb-4 max-h-48 overflow-y-auto space-y-1">
        <p
          v-for="(log, i) in store.logs"
          :key="i"
          class="text-sm font-mono"
          :class="{
            'text-red-400': log.type === 'error',
            'text-cyan-300': log.type === 'step',
            'text-gray-400': log.type === 'info',
          }"
        >
          <span class="text-gray-600 mr-2">{{ formatTime(log.timestamp) }}</span>
          {{ log.message }}
        </p>
      </div>
    </details>

    <div class="text-center">
      <button
        @click="store.resetToInput()"
        class="px-6 py-2 text-sm text-gray-400 hover:text-gray-200 border border-gray-700 hover:border-gray-500 rounded-lg transition-all"
      >
        Cancel
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteBuilderStore, PIPELINE_STEPS } from '../stores/siteBuilderStore'

const store = useSiteBuilderStore()
const steps = PIPELINE_STEPS

const progressPercent = computed(() => {
  const total = steps.length
  const completed = steps.filter(s => store.completedSteps.has(s.key)).length
  const hasActive = store.activeStep ? 0.5 : 0
  return Math.round(((completed + hasActive) / total) * 100)
})

function stepIconClass(key: string): string {
  const status = store.stepStatus(key)
  if (status === 'completed') return 'bg-cyan-500 shadow-lg shadow-cyan-500/20'
  if (status === 'active') return 'bg-cyan-500/20 ring-2 ring-cyan-400 ring-offset-2 ring-offset-gray-900'
  return 'bg-gray-700'
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch { return '' }
}
</script>
