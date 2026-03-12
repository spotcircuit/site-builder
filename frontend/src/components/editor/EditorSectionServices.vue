<template>
  <EditorAccordion title="Services" icon="S" sectionId="services">
    <div class="space-y-3">
      <div
        v-for="(svc, i) in services"
        :key="i"
        class="bg-gray-800/50 rounded-lg p-3 space-y-2 relative group"
      >
        <!-- Item controls -->
        <div class="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            v-if="i > 0"
            @click="store.moveEditableArrayItem('services', i, 'up')"
            class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
            title="Move up"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button
            v-if="i < services.length - 1"
            @click="store.moveEditableArrayItem('services', i, 'down')"
            class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
            title="Move down"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button
            @click="store.removeEditableArrayItem('services', i)"
            class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700"
            title="Remove"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <input
          :value="svc.name || ''"
          @input="store.updateEditableField(`services.${i}.name`, ($event.target as HTMLInputElement).value)"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Service name"
        />
        <RichTextField
          :modelValue="svc.description || ''"
          @update:modelValue="store.updateEditableField(`services.${i}.description`, $event)"
          :rows="3"
        />
      </div>

      <ImageField
        label="Services Section Image"
        :modelValue="store.editableData?.ai_services_image || ''"
        @update:modelValue="store.updateEditableField('ai_services_image', $event)"
      />

      <div class="flex gap-2">
        <button
          @click="store.addEditableArrayItem('services', { name: '', description: '', icon_suggestion: 'star' })"
          class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors"
        >+ Add Service</button>
        <button
          @click="$emit('generate', 'services')"
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
import RichTextField from './RichTextField.vue'

defineEmits<{ generate: [sectionType: string] }>()
const store = useSiteBuilderStore()
const services = computed(() => store.editableData?.services || [])
</script>
