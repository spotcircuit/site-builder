<template>
  <EditorAccordion title="Design" icon="D" sectionId="hero">
    <div class="space-y-3">
      <p class="text-xs text-amber-400/80">Color and font changes require "Apply Changes" to take effect.</p>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Primary Color</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              :value="store.editableData?.color_primary || '#2563EB'"
              @input="store.updateEditableField('color_primary', ($event.target as HTMLInputElement).value)"
              class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent"
            />
            <input
              :value="store.editableData?.color_primary || '#2563EB'"
              @input="store.updateEditableField('color_primary', ($event.target as HTMLInputElement).value)"
              class="flex-1 px-2 py-1.5 rounded-lg bg-gray-800 border border-gray-600 text-white text-xs font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Secondary Color</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              :value="store.editableData?.color_secondary || '#F59E0B'"
              @input="store.updateEditableField('color_secondary', ($event.target as HTMLInputElement).value)"
              class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent"
            />
            <input
              :value="store.editableData?.color_secondary || '#F59E0B'"
              @input="store.updateEditableField('color_secondary', ($event.target as HTMLInputElement).value)"
              class="flex-1 px-2 py-1.5 rounded-lg bg-gray-800 border border-gray-600 text-white text-xs font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Heading Font</label>
          <select
            :value="store.editableData?.font_heading || 'Inter'"
            @change="store.updateEditableField('font_heading', ($event.target as HTMLSelectElement).value)"
            class="w-full px-2 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option v-for="font in fonts" :key="font" :value="font">{{ font }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Body Font</label>
          <select
            :value="store.editableData?.font_body || 'Inter'"
            @change="store.updateEditableField('font_body', ($event.target as HTMLSelectElement).value)"
            class="w-full px-2 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option v-for="font in fonts" :key="font" :value="font">{{ font }}</option>
          </select>
        </div>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()

const fonts = [
  'Inter', 'Montserrat', 'Poppins', 'Raleway', 'Playfair Display',
  'Lato', 'Open Sans', 'Roboto', 'Source Sans Pro', 'Nunito',
  'DM Sans', 'Outfit', 'Space Grotesk', 'Sora', 'Manrope',
  'Merriweather', 'Lora', 'Crimson Text', 'Work Sans', 'Rubik',
]
</script>
