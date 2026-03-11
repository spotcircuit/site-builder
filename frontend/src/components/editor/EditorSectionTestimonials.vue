<template>
  <EditorAccordion title="Testimonials" icon="T" sectionId="testimonials">
    <div class="space-y-3">
      <div
        v-for="(t, i) in testimonials"
        :key="i"
        class="bg-gray-800/50 rounded-lg p-3 space-y-2 relative group"
      >
        <div class="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button v-if="i > 0" @click="store.moveEditableArrayItem('testimonials', i, 'up')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move up">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button v-if="i < testimonials.length - 1" @click="store.moveEditableArrayItem('testimonials', i, 'down')" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move down">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button @click="store.removeEditableArrayItem('testimonials', i)" class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700" title="Remove">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div class="flex gap-2">
          <input
            :value="t.author || ''"
            @input="store.updateEditableField(`testimonials.${i}.author`, ($event.target as HTMLInputElement).value)"
            class="flex-1 px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="Author name"
          />
          <div class="flex items-center gap-1">
            <button
              v-for="star in 5" :key="star"
              @click="store.updateEditableField(`testimonials.${i}.rating`, star)"
              class="text-lg leading-none"
              :class="star <= (t.rating || 5) ? 'text-yellow-400' : 'text-gray-600'"
            >&#9733;</button>
          </div>
        </div>
        <textarea
          :value="t.text || ''"
          @input="store.updateEditableField(`testimonials.${i}.text`, ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
          placeholder="Review text..."
        ></textarea>
      </div>

      <div class="flex gap-2">
        <button
          @click="store.addEditableArrayItem('testimonials', { author: '', rating: 5, text: '' })"
          class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors"
        >+ Add Testimonial</button>
        <button
          @click="$emit('generate', 'testimonials')"
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

defineEmits<{ generate: [sectionType: string] }>()
const store = useSiteBuilderStore()
const testimonials = computed(() => store.editableData?.testimonials || [])
</script>
