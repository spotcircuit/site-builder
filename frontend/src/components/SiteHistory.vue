<template>
  <div v-if="completedSites.length > 0" class="mt-12">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">Generated Sites</h3>
      <span class="text-sm text-gray-500">{{ completedSites.length }} site{{ completedSites.length === 1 ? '' : 's' }}</span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="site in completedSites"
        :key="site.jobId"
        class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden hover:border-gray-600 transition-all group"
      >
        <!-- Thumbnail -->
        <div class="h-32 bg-gray-900 flex items-center justify-center relative">
          <div class="text-center">
            <span class="text-3xl">&#127760;</span>
            <p class="text-xs text-emerald-400 mt-1">Ready</p>
          </div>

          <!-- Delete button -->
          <button
            @click.stop="store.deleteSite(site.jobId)"
            class="absolute top-2 right-2 w-7 h-7 rounded-full bg-gray-800/80 text-gray-400 hover:text-red-400 hover:bg-gray-700 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
            title="Delete"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Info -->
        <div class="p-3">
          <h4 class="font-medium text-white text-sm truncate">
            {{ site.businessName }}
          </h4>
          <p class="text-xs text-gray-500 mt-1">
            {{ formatDate(site.createdAt) }}
          </p>

          <!-- Actions -->
          <div class="flex gap-2 mt-3">
            <a
              v-if="site.deployUrl"
              :href="site.deployUrl"
              target="_blank"
              class="flex-1 py-1.5 text-xs font-medium rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-all text-center"
            >
              Visit Site
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteBuilderStore } from '../stores/siteBuilderStore'

const store = useSiteBuilderStore()

// Only show completed sites with a real business name — hide stale "generating" entries
const completedSites = computed(() =>
  store.siteHistory.filter(s =>
    s.status === 'completed' && s.businessName && s.businessName !== 'Generating...'
  )
)

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  } catch { return '' }
}
</script>
