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
            <p class="text-xs text-gray-500 -mt-0.5">URL to Website in 60 seconds</p>
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
    <main class="flex-1 w-full" :class="store.phase === 'result' ? '' : 'max-w-6xl mx-auto px-6 py-8'">

      <!-- INPUT PHASE -->
      <section v-if="store.phase === 'input'" class="space-y-8">
        <!-- Hero -->
        <div class="text-center mb-8 pt-8">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-6">
            <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            AI-Powered Site Generation
          </div>
          <h2 class="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            Any Business, Any URL,<br>
            <span class="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">Get a Premium Website</span>
          </h2>
          <p class="text-gray-400 text-lg max-w-2xl mx-auto">
            Paste a Google Maps link or any website URL and generate a beautiful, client-ready React website with AI-generated content and images. Deploy instantly.
          </p>
        </div>

        <!-- Input Card -->
        <div class="max-w-3xl mx-auto">
          <div class="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 space-y-5">
            <!-- Business Search (Places Autocomplete + Any URL) -->
            <PlacesAutocomplete
              :disabled="store.isGenerating"
              @select="onPlaceSelect"
              @website-url="onWebsiteUrl"
              @clear="onPlaceClear"
            />

            <!-- Business Name & Category (shown for website-only URLs) -->
            <transition name="slide-fade">
              <div v-if="store.inputUrlType === 'website'" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">
                      What's the business called?
                    </label>
                    <input
                      v-model="store.businessNameInput"
                      type="text"
                      placeholder="e.g. Joe's Pizza"
                      class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all"
                      :class="store.businessNameInput.trim() ? 'border-gray-600' : 'border-cyan-500/40'"
                      :disabled="store.isGenerating"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-300 mb-2">
                      Category
                      <span class="text-gray-500 font-normal">(optional)</span>
                    </label>
                    <input
                      v-model="store.businessCategoryInput"
                      type="text"
                      placeholder="e.g. Italian Restaurant"
                      class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all"
                      :disabled="store.isGenerating"
                    />
                  </div>
                </div>
                <!-- Cross-pollination hint -->
                <div class="flex items-start gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/50">
                  <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <p class="text-xs text-gray-400">
                    <span class="text-gray-300">Want richer results?</span>
                    Paste a Google Maps link instead to pull in real photos, reviews, hours, and contact info.
                  </p>
                </div>
              </div>
            </transition>

            <!-- Website URL Enhancement (only when Maps URL is used) -->
            <transition name="slide-fade">
              <div v-if="store.inputUrlType === 'maps'" class="space-y-2">
                <label class="block text-sm font-medium text-gray-300">
                  Add their website for even better results
                  <span class="text-gray-500 font-normal">(optional)</span>
                </label>
                <input
                  v-model="store.websiteUrl"
                  type="url"
                  placeholder="https://example.com"
                  class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all"
                  :disabled="store.isGenerating"
                />
                <p class="text-xs text-gray-500 pl-1">We'll pull their real branding, colors, and images</p>
              </div>
            </transition>

            <!-- Business Context (optional) -->
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Business Context
                <span class="text-gray-500 font-normal">(optional — helps AI write accurate content)</span>
              </label>
              <textarea
                v-model="store.businessContext"
                rows="3"
                placeholder="e.g. Family-owned Italian restaurant since 1985, known for wood-fired pizza and homemade pasta. Open for lunch and dinner, with outdoor seating and private event space."
                class="w-full px-4 py-3 rounded-xl bg-gray-900/50 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-all resize-none"
                :disabled="store.isGenerating"
              ></textarea>
            </div>

            <!-- Template Selection -->
            <TemplateCards
              :selected="store.templateName"
              @select="store.templateName = $event"
            />

            <!-- Cloudflare Turnstile (anti-abuse) -->
            <div
              v-if="turnstileSiteKey"
              ref="turnstileRef"
              class="cf-turnstile flex justify-center"
              :data-sitekey="turnstileSiteKey"
              data-callback="onTurnstileSuccess"
              data-theme="dark"
              data-size="flexible"
            ></div>

            <!-- Generate Button -->
            <button
              @click="store.startGeneration()"
              :disabled="!store.canGenerate || (turnstileSiteKey && !store.turnstileToken)"
              class="w-full py-4 rounded-xl font-bold text-lg transition-all duration-200 flex items-center justify-center gap-3"
              :class="
                !store.canGenerate
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
      <section v-if="store.phase === 'result'">
        <!-- Top bar: title + actions -->
        <div class="flex items-center justify-between px-6 py-3 border-b border-gray-700/50 bg-gray-800/50">
          <div class="flex items-center gap-4">
            <div>
              <h2 class="text-lg font-bold text-white">
                {{ store.resultBusinessName || 'Site Ready' }}
              </h2>
              <p class="text-xs text-gray-400">{{ store.resultTitle }}</p>
            </div>
            <!-- Deploy badge -->
            <a
              v-if="store.resultDeployUrl"
              :href="store.resultDeployUrl"
              target="_blank"
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-900/40 border border-emerald-600/30 text-emerald-400 text-xs font-medium hover:bg-emerald-900/60 transition-colors"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Live
            </a>
          </div>
          <div class="flex items-center gap-2">
            <!-- Toggle editor -->
            <button
              @click="store.editorOpen ? store.closeEditor() : store.openEditor()"
              class="px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2"
              :class="store.editorOpen
                ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20'
                : 'bg-cyan-600 hover:bg-cyan-500 text-white'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              {{ store.editorOpen ? 'Hide Editor' : 'Edit Site' }}
            </button>
            <a
              v-if="store.resultDeployUrl"
              :href="store.resultDeployUrl"
              target="_blank"
              class="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-all"
            >Visit Site</a>
            <a
              :href="store.downloadUrl"
              target="_blank"
              class="px-4 py-2 rounded-lg border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white text-sm font-semibold transition-all"
            >Download</a>
            <button
              @click="store.resetToInput()"
              class="px-4 py-2 rounded-lg border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white text-sm font-semibold transition-all"
            >New Site</button>
          </div>
        </div>

        <!-- Editor (left) + Preview (right) layout -->
        <div class="flex">
          <!-- Editor Panel - left side, always visible when open -->
          <EditorPanel v-if="store.editorOpen" />

          <!-- Preview area -->
          <div class="flex-1 min-w-0 p-4">
            <DevicePreview :html="store.resultHtml" />
          </div>
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
import { onMounted, onUnmounted, ref } from 'vue'
import { useSiteBuilderStore } from './stores/siteBuilderStore'

// Cloudflare Turnstile — site key is public (visible in page source by design)
const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY || '0x4AAAAAACp0MDK6rlOaKzf4'
const turnstileRef = ref<HTMLElement | null>(null)
import DevicePreview from './components/DevicePreview.vue'
import PlacesAutocomplete from './components/PlacesAutocomplete.vue'
import ProgressPanel from './components/ProgressPanel.vue'
import SiteHistory from './components/SiteHistory.vue'
import SeoScorePanel from './components/SeoScorePanel.vue'
import EditorPanel from './components/editor/EditorPanel.vue'
import TemplateCards from './components/TemplateCards.vue'

const store = useSiteBuilderStore()

function onPlaceSelect(place: { name: string; address: string; placeId: string | null; mapsUrl: string }) {
  store.setInputUrl(place.mapsUrl)
}

function onWebsiteUrl(url: string) {
  store.setInputUrl(url)
}

function onPlaceClear() {
  store.setInputUrl('')
  store.businessNameInput = ''
  store.businessCategoryInput = ''
}

onMounted(() => {
  store.initWebSocket()
  store.loadSiteHistory()
  store.loadTemplates()

  // Load Cloudflare Turnstile script if configured
  if (turnstileSiteKey) {
    ;(window as any).onTurnstileSuccess = (token: string) => {
      store.turnstileToken = token
    }
    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }
})

onUnmounted(() => {
  store.destroyWebSocket()
})
</script>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}
.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
