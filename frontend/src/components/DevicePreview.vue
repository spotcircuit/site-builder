<template>
  <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
    <!-- Browser chrome bar -->
    <div class="flex items-center justify-between px-4 py-2.5 bg-gray-800 border-b border-gray-700/50">
      <div class="flex items-center gap-3">
        <div class="flex gap-1.5">
          <div class="w-3 h-3 rounded-full bg-red-500/60"></div>
          <div class="w-3 h-3 rounded-full bg-yellow-500/60"></div>
          <div class="w-3 h-3 rounded-full bg-green-500/60"></div>
        </div>
        <span class="text-xs text-gray-500 ml-1">Preview</span>
      </div>

      <!-- Device Toggles -->
      <div class="flex items-center gap-1 bg-gray-900/50 rounded-lg p-1">
        <button
          v-for="device in devices"
          :key="device.key"
          @click="store.previewDevice = device.key"
          class="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200"
          :class="store.previewDevice === device.key
            ? 'bg-cyan-600 text-white shadow-sm'
            : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
        >
          <span class="mr-1">{{ device.icon }}</span>
          {{ device.label }}
        </button>
      </div>
    </div>

    <!-- Preview Frame -->
    <div
      class="bg-gray-900 flex justify-center overflow-hidden transition-all duration-300"
      style="min-height: 500px;"
    >
      <div
        class="transition-all duration-300 ease-in-out bg-white"
        :style="{ width: store.previewWidth, maxWidth: '100%' }"
      >
        <iframe
          v-if="previewHtml"
          ref="iframeEl"
          :srcdoc="previewHtml"
          class="w-full bg-white"
          :style="{ height: frameHeight, border: 'none' }"
          sandbox="allow-scripts allow-same-origin allow-popups"
        ></iframe>
        <div v-if="!previewHtml" class="flex items-center justify-center h-96 text-gray-500">
          No preview available
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useSiteBuilderStore } from '../stores/siteBuilderStore'

const props = defineProps<{ html: string | null }>()
const store = useSiteBuilderStore()
const iframeEl = ref<HTMLIFrameElement | null>(null)

// Expose iframe ref to store for Quick Preview postMessage
watch(iframeEl, (el) => {
  store.iframeRef = el
})

onMounted(() => {
  if (iframeEl.value) {
    store.iframeRef = iframeEl.value
  }
})

const devices = [
  { key: 'desktop' as const, label: 'Desktop', icon: '🖥️' },
  { key: 'tablet' as const, label: 'Tablet', icon: '📱' },
  { key: 'mobile' as const, label: 'Mobile', icon: '📲' },
]

const frameHeight = computed(() => {
  switch (store.previewDevice) {
    case 'mobile': return '667px'
    case 'tablet': return '600px'
    default: return '700px'
  }
})

// Inject a script that intercepts link clicks inside the preview iframe
// - Hash links (#about) scroll smoothly within the iframe
// - External links open in a new tab instead of navigating the iframe away
const PREVIEW_LINK_HANDLER = `<script>
document.addEventListener('click', function(e) {
  var link = e.target.closest('a');
  if (!link) return;
  var href = link.getAttribute('href');
  if (!href) return;
  e.preventDefault();
  if (href.startsWith('#')) {
    var target = document.querySelector(href);
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  } else if (href.startsWith('http') || href.startsWith('//')) {
    window.open(href, '_blank', 'noopener');
  }
});
// Also intercept form submissions
document.addEventListener('submit', function(e) { e.preventDefault(); });
// Scroll to section when editor accordion is opened
window.addEventListener('message', function(e) {
  if (e.data && e.data.type === 'SCROLL_TO_SECTION' && e.data.sectionId) {
    var el = document.getElementById(e.data.sectionId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  if (e.data && e.data.type === 'QUICK_PREVIEW' && e.data.payload) {
    // Quick preview handled by React's own listener if present
  }
});
<\/script>`

const previewHtml = computed(() => {
  if (!props.html) return null
  // Inject the link handler before </body>
  if (props.html.includes('</body>')) {
    return props.html.replace('</body>', PREVIEW_LINK_HANDLER + '</body>')
  }
  return props.html + PREVIEW_LINK_HANDLER
})
</script>
