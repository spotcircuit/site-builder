<template>
  <div class="border border-gray-700/50 rounded-lg">
    <button
      @click="toggle"
      class="w-full flex items-center justify-between px-4 py-3 bg-gray-800/80 hover:bg-gray-700/50 transition-colors text-left rounded-t-lg"
      :class="{ 'rounded-b-lg': !isOpen }"
    >
      <div class="flex items-center gap-2">
        <span v-if="icon" class="text-sm">{{ icon }}</span>
        <span class="text-sm font-medium text-gray-200">{{ title }}</span>
      </div>
      <svg
        class="w-4 h-4 text-gray-400 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    <div v-if="isOpen" class="px-4 py-5 space-y-4 bg-gray-900/30 border-t border-gray-700/30 min-h-[180px]">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'

const props = withDefaults(defineProps<{
  title: string
  icon?: string
  defaultOpen?: boolean
  sectionId?: string
}>(), {
  defaultOpen: false,
})

const store = useSiteBuilderStore()
const isOpen = ref(props.defaultOpen)

function scrollToSection() {
  if (!props.sectionId) return
  const iframe = store.iframeRef
  if (iframe?.contentWindow) {
    iframe.contentWindow.postMessage(
      { type: 'SCROLL_TO_SECTION', sectionId: props.sectionId },
      '*',
    )
  }
}

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value && props.sectionId) {
    // Small delay to ensure iframe is ready to receive the message
    setTimeout(scrollToSection, 100)
  }
}
</script>
