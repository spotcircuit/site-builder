<template>
  <EditorAccordion title="Call to Action" icon="C" sectionId="cta">
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">CTA Headline</label>
        <input
          :value="store.editableData?.cta_headline || ''"
          @input="store.updateEditableField('cta_headline', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Button Text</label>
        <input
          :value="store.editableData?.cta_button_text || ''"
          @input="store.updateEditableField('cta_button_text', ($event.target as HTMLInputElement).value)"
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
