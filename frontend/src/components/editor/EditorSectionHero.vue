<template>
  <EditorAccordion title="Hero" icon="H" :defaultOpen="true" sectionId="hero">
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Headline</label>
        <input
          :value="store.editableData?.hero_headline || ''"
          @input="store.updateEditableField('hero_headline', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Main headline..."
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Subheadline</label>
        <textarea
          :value="store.editableData?.hero_subheadline || ''"
          @input="store.updateEditableField('hero_subheadline', ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
          placeholder="Supporting text..."
        ></textarea>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()
</script>
