<template>
  <EditorAccordion title="SEO & Social" icon="S" sectionId="hero">
    <div class="space-y-3">
      <div>
        <div class="flex justify-between items-center mb-1">
          <label class="text-xs font-medium text-gray-400">Page Title</label>
          <span class="text-xs" :class="(store.editableData?.seo_title || '').length > 60 ? 'text-red-400' : 'text-gray-500'">
            {{ (store.editableData?.seo_title || '').length }}/60
          </span>
        </div>
        <input
          :value="store.editableData?.seo_title || ''"
          @input="store.updateEditableField('seo_title', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>
      <div>
        <div class="flex justify-between items-center mb-1">
          <label class="text-xs font-medium text-gray-400">Meta Description</label>
          <span class="text-xs" :class="(store.editableData?.seo_description || '').length > 160 ? 'text-red-400' : 'text-gray-500'">
            {{ (store.editableData?.seo_description || '').length }}/160
          </span>
        </div>
        <textarea
          :value="store.editableData?.seo_description || ''"
          @input="store.updateEditableField('seo_description', ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
        ></textarea>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">OG Title (Social)</label>
        <input
          :value="store.editableData?.og_title || ''"
          @input="store.updateEditableField('og_title', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">OG Description (Social)</label>
        <textarea
          :value="store.editableData?.og_description || ''"
          @input="store.updateEditableField('og_description', ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
        ></textarea>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">OG Image URL</label>
        <input
          :value="store.editableData?.og_image || ''"
          @input="store.updateEditableField('og_image', ($event.target as HTMLInputElement).value)"
          placeholder="https://example.com/image.jpg"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
        <p class="text-xs text-gray-500 mt-1">Recommended: 1200x630px for best social sharing</p>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Canonical URL</label>
        <input
          :value="store.editableData?.canonical_url || ''"
          @input="store.updateEditableField('canonical_url', ($event.target as HTMLInputElement).value)"
          placeholder="https://yourdomain.com"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'
const store = useSiteBuilderStore()
</script>
