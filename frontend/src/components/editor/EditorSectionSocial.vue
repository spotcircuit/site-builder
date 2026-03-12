<template>
  <EditorAccordion title="Social Links" icon="S">
    <div class="space-y-2.5">
      <div v-for="platform in platforms" :key="platform.key" class="flex items-center gap-2">
        <div class="w-7 h-7 flex-shrink-0 flex items-center justify-center rounded bg-gray-800 text-gray-400">
          <span class="text-xs font-bold uppercase">{{ platform.key.charAt(0) }}</span>
        </div>
        <input
          :value="getSocialUrl(platform.key)"
          @input="setSocialUrl(platform.key, ($event.target as HTMLInputElement).value)"
          class="flex-1 px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          :placeholder="platform.placeholder"
        />
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()

const platforms = [
  { key: 'facebook', placeholder: 'https://facebook.com/...' },
  { key: 'instagram', placeholder: 'https://instagram.com/...' },
  { key: 'twitter', placeholder: 'https://x.com/...' },
  { key: 'linkedin', placeholder: 'https://linkedin.com/in/...' },
  { key: 'youtube', placeholder: 'https://youtube.com/@...' },
  { key: 'tiktok', placeholder: 'https://tiktok.com/@...' },
  { key: 'yelp', placeholder: 'https://yelp.com/biz/...' },
]

function getSocialUrl(platform: string): string {
  const links = store.editableData?.social_links
  if (!links || typeof links !== 'object') return ''
  return (links as Record<string, string>)[platform] || ''
}

function setSocialUrl(platform: string, url: string) {
  if (!store.editableData) return
  if (!store.editableData.social_links || typeof store.editableData.social_links !== 'object') {
    store.editableData.social_links = {}
  }
  store.updateEditableField(`social_links.${platform}`, url)
}
</script>
