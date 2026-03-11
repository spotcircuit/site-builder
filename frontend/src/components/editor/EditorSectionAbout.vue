<template>
  <EditorAccordion title="About" icon="A" sectionId="about">
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Section Title</label>
        <input
          :value="store.editableData?.about_title || ''"
          @input="store.updateEditableField('about_title', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">About Text</label>
        <textarea
          :value="store.editableData?.about_text || ''"
          @input="store.updateEditableField('about_text', ($event.target as HTMLTextAreaElement).value)"
          rows="5"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
        ></textarea>
      </div>
      <ImageField
        label="About Section Image"
        :modelValue="store.editableData?.ai_about_image || ''"
        @update:modelValue="store.updateEditableField('ai_about_image', $event)"
      />
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'
import ImageField from './ImageField.vue'
const store = useSiteBuilderStore()
</script>
