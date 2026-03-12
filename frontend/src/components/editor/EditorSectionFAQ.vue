<template>
  <EditorAccordion title="FAQ" icon="?" sectionId="faq">
    <div class="space-y-3">
      <div
        v-for="(faq, i) in faqs"
        :key="i"
        class="bg-gray-800/50 rounded-lg p-3 space-y-2 relative group"
      >
        <div class="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button v-if="i > 0" @click="store.moveEditableArrayItem('faq_items', i, 'up')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move up">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button v-if="i < faqs.length - 1" @click="store.moveEditableArrayItem('faq_items', i, 'down')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move down">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button @click="store.removeEditableArrayItem('faq_items', i)" class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700" title="Remove">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <input
          :value="faq.question || ''"
          @input="store.updateEditableField(`faq_items.${i}.question`, ($event.target as HTMLInputElement).value)"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Question"
        />
        <RichTextField
          :modelValue="faq.answer || ''"
          @update:modelValue="store.updateEditableField(`faq_items.${i}.answer`, $event)"
          :rows="3"
        />
      </div>

      <div class="flex gap-2">
        <button
          @click="store.addEditableArrayItem('faq_items', { question: '', answer: '' })"
          class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors"
        >+ Add FAQ</button>
        <button
          @click="$emit('generate', 'faq_items')"
          class="px-4 py-2 rounded-lg bg-purple-600/20 border border-purple-500/30 text-purple-300 hover:bg-purple-600/30 text-sm transition-colors"
        >AI Generate</button>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'
import RichTextField from './RichTextField.vue'

defineEmits<{ generate: [sectionType: string] }>()
const store = useSiteBuilderStore()
const faqs = computed(() => store.editableData?.faq_items || [])
</script>
