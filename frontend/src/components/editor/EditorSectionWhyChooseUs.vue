<template>
  <EditorAccordion title="Why Choose Us" icon="W" sectionId="why-choose-us">
    <div class="space-y-3">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="bg-gray-800/50 rounded-lg p-3 space-y-2 relative group"
      >
        <div class="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button v-if="i > 0" @click="store.moveEditableArrayItem('why_choose_us', i, 'up')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move up">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button v-if="i < items.length - 1" @click="store.moveEditableArrayItem('why_choose_us', i, 'down')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move down">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button @click="store.removeEditableArrayItem('why_choose_us', i)" class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700" title="Remove">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <input
          :value="item.title || ''"
          @input="store.updateEditableField(`why_choose_us.${i}.title`, ($event.target as HTMLInputElement).value)"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Title"
        />
        <textarea
          :value="item.description || ''"
          @input="store.updateEditableField(`why_choose_us.${i}.description`, ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
          placeholder="Description..."
        ></textarea>
        <input
          :value="item.icon_key || ''"
          @input="store.updateEditableField(`why_choose_us.${i}.icon_key`, ($event.target as HTMLInputElement).value)"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Icon key (e.g. shield, star, clock)"
        />
      </div>

      <ImageField
        label="Why Choose Us Image"
        :modelValue="store.editableData?.ai_why_choose_us_image || ''"
        @update:modelValue="store.updateEditableField('ai_why_choose_us_image', $event)"
      />

      <div class="flex gap-2">
        <button
          @click="store.addEditableArrayItem('why_choose_us', { title: '', description: '', icon_key: 'star' })"
          class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors"
        >+ Add Reason</button>
        <button
          @click="$emit('generate', 'why_choose_us')"
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
import ImageField from './ImageField.vue'

defineEmits<{ generate: [sectionType: string] }>()
const store = useSiteBuilderStore()
const items = computed(() => store.editableData?.why_choose_us || [])
</script>
