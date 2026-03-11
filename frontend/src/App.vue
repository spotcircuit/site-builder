<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
    <!-- Header -->
    <header class="border-b border-gray-700/50 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3 cursor-pointer" @click="store.resetToInput()">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
            </svg>
          </div>
          <div>
            <h1 class="text-lg font-bold tracking-tight">Site Builder</h1>
            <p class="text-xs text-gray-500 -mt-0.5">Maps to Website in 60 seconds</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <span
              class="inline-block w-2 h-2 rounded-full animate-pulse"
              :class="store.wsConnected ? 'bg-green-400' : 'bg-red-400'"
            ></span>
            {{ store.wsConnected ? 'Connected' : 'Disconnected' }}
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-6 py-8">

      <!-- INPUT PHASE -->
      <section v-if="store.phase === 'input'" class="space-y-8">
        <!-- Hero -->
        <div class="text-center mb-8 pt-8">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-6">
            <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            AI-Powered Site Generation
          </div>
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            Search Any Business,<br>
            <span class="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">Get a Premium Website</span>
          </h2>
          <p class="text-gray-400 text-lg max-w-2xl mx-auto">
            Find any business by name and generate a beautiful, client-ready React website with AI-generated content and images. Deploy instantly.
          </p>
        </div>

        <!-- Input Card -->
        <div class="max-w-3xl mx-auto">
          <div class="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 space-y-5">
            <!-- Business Search (Places Autocomplete) -->
            <PlacesAutocomplete
              :disabled="store.isGenerating"
              @select="onPlaceSelect"
              @clear="onPlaceClear"
            />

            <div class="grid grid-cols-2 gap-4">
              <!-- Template -->
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Template</label>
                <select
                  v-model="store.templateName"
                  class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all"
                  :disabled="store.isGenerating"
                >
                  <option value="modern">Modern (React)</option>
                </select>
              </div>

              <!-- Deploy target is always auto-detect -->
            </div>

            <!-- Generate Button -->
            <button
              @click="store.startGeneration()"
              :disabled="!store.mapsUrl.trim() || store.isGenerating"
              class="w-full py-4 rounded-xl font-bold text-lg transition-all duration-200 flex items-center justify-center gap-3"
              :class="
                !store.mapsUrl.trim() || store.isGenerating
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-lg shadow-cyan-600/20 hover:shadow-cyan-500/30 cursor-pointer hover:scale-[1.01] active:scale-[0.99]'
              "
            >
              <svg v-if="!store.isGenerating" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <svg v-else class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              {{ store.isGenerating ? 'Generating...' : 'Generate Site' }}
            </button>
          </div>

          <!-- Feature chips -->
          <div class="flex flex-wrap justify-center gap-3 mt-6">
            <span class="px-3 py-1 rounded-full bg-gray-800/50 border border-gray-700/50 text-xs text-gray-400">AI Content</span>
            <span class="px-3 py-1 rounded-full bg-gray-800/50 border border-gray-700/50 text-xs text-gray-400">Gemini Images</span>
            <span class="px-3 py-1 rounded-full bg-gray-800/50 border border-gray-700/50 text-xs text-gray-400">React + Tailwind</span>
            <span class="px-3 py-1 rounded-full bg-gray-800/50 border border-gray-700/50 text-xs text-gray-400">Auto Deploy</span>
            <span class="px-3 py-1 rounded-full bg-gray-800/50 border border-gray-700/50 text-xs text-gray-400">SEO Optimized</span>
          </div>
        </div>

        <!-- Site History Dashboard -->
        <SiteHistory />
      </section>

      <!-- PROGRESS PHASE -->
      <ProgressPanel v-if="store.phase === 'progress'" />

      <!-- RESULT PHASE -->
      <section v-if="store.phase === 'result'" class="space-y-6">
        <div class="text-center mb-4">
          <h2 class="text-2xl font-bold text-white mb-1">
            {{ store.resultTitle || 'Site Ready' }}
          </h2>
          <p class="text-gray-400">
            Website for <span class="text-cyan-400 font-medium">{{ store.resultBusinessName }}</span> has been generated.
          </p>
        </div>

        <!-- Deploy URL Banner -->
        <div
          v-if="store.resultDeployUrl"
          class="bg-emerald-900/30 border border-emerald-600/30 rounded-xl p-4 flex items-center justify-between"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p class="text-emerald-300 font-semibold text-sm">
                Live on {{ store.resultDeployProvider === 'cloudflare' ? 'Cloudflare Pages' : 'Vercel' }}
              </p>
              <a
                :href="store.resultDeployUrl"
                target="_blank"
                class="text-emerald-400 hover:text-emerald-300 underline text-sm"
              >
                {{ store.resultDeployUrl }}
              </a>
            </div>
          </div>
          <a
            :href="store.resultDeployUrl"
            target="_blank"
            class="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-all shadow-lg shadow-emerald-600/20"
          >
            Visit Live Site
          </a>
        </div>

        <!-- Device Preview + SEO Panel -->
        <div class="flex gap-6 items-start">
          <div class="flex-1 min-w-0">
            <DevicePreview :html="store.resultHtml" />
          </div>
          <SeoScorePanel
            v-if="store.seoData"
            :business-name="store.resultBusinessName"
            :rating="store.seoData.rating"
            :review-count="store.seoData.review_count"
            :has-phone="store.seoData.has_phone"
            :has-address="store.seoData.has_address"
            :has-website="store.seoData.has_website"
            :has-hours="store.seoData.has_hours"
            :has-photos="store.seoData.has_photos"
            :has-reviews="store.seoData.has_reviews"
            :category="store.seoData.category"
            :seo-title="store.seoData.seo_title"
            :seo-description="store.seoData.seo_description"
          />
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center justify-center gap-4">
          <a
            v-if="store.resultDeployUrl"
            :href="store.resultDeployUrl"
            target="_blank"
            class="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-all shadow-lg"
          >
            Visit Live Site
          </a>
          <a
            :href="store.downloadUrl"
            target="_blank"
            class="px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-all shadow-lg"
          >
            Download HTML
          </a>
          <button
            @click="store.resetToInput()"
            class="px-6 py-3 rounded-xl border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white font-semibold transition-all"
          >
            Generate Another
          </button>
        </div>
      </section>

      <!-- ERROR PHASE -->
      <section v-if="store.phase === 'error'" class="space-y-6">
        <div class="bg-red-900/20 border border-red-700/50 rounded-xl p-6">
          <h3 class="text-red-400 font-semibold text-lg mb-2">Generation Failed</h3>
          <p class="text-red-300">{{ store.errorMessage }}</p>
          <pre
            v-if="store.errorDetails"
            class="mt-4 text-xs text-red-300/70 bg-red-900/20 rounded-lg p-4 overflow-x-auto max-h-48 overflow-y-auto"
          >{{ store.errorDetails }}</pre>
        </div>
        <div class="text-center">
          <button
            @click="store.resetToInput()"
            class="px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-all"
          >
            Try Again
          </button>
        </div>
      </section>

    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-4 text-center text-xs text-gray-600">
      Site Builder &middot; Powered by Claude AI + Gemini &middot; React + TailwindCSS
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useSiteBuilderStore } from './stores/siteBuilderStore'
import DevicePreview from './components/DevicePreview.vue'
import PlacesAutocomplete from './components/PlacesAutocomplete.vue'
import ProgressPanel from './components/ProgressPanel.vue'
import SiteHistory from './components/SiteHistory.vue'
import SeoScorePanel from './components/SeoScorePanel.vue'

const store = useSiteBuilderStore()

function onPlaceSelect(place: { name: string; address: string; placeId: string | null; mapsUrl: string }) {
  store.mapsUrl = place.mapsUrl
}

function onPlaceClear() {
  store.mapsUrl = ''
}

onMounted(() => {
  store.initWebSocket()
  store.loadSiteHistory()
})

onUnmounted(() => {
  store.destroyWebSocket()
})
</script>
