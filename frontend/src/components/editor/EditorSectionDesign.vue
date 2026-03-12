<template>
  <EditorAccordion title="Design" icon="D" sectionId="hero">
    <div class="space-y-3">
      <p class="text-xs text-amber-400/80">Color and font changes require "Apply Changes" to take effect.</p>

      <!-- Theme Presets -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-2">Quick Themes</label>
        <div class="grid grid-cols-4 gap-2">
          <button
            v-for="theme in themes"
            :key="theme.name"
            @click="applyTheme(theme)"
            class="group relative rounded-lg p-1.5 border transition-all hover:scale-105"
            :class="isActiveTheme(theme) ? 'border-cyan-500 bg-gray-700/50' : 'border-gray-700 hover:border-gray-500'"
            :title="theme.name"
          >
            <div class="flex gap-0.5 mb-1">
              <div class="w-4 h-4 rounded-sm" :style="{ backgroundColor: theme.primary }"></div>
              <div class="w-4 h-4 rounded-sm" :style="{ backgroundColor: theme.secondary }"></div>
            </div>
            <span class="text-[10px] text-gray-400 group-hover:text-white block truncate">{{ theme.name }}</span>
          </button>
        </div>
      </div>

      <!-- Color Pickers -->
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

      <!-- Font Selectors -->
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

      <!-- Font Scale -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1.5">Text Size</label>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="scale in fontScales"
            :key="scale.value"
            @click="store.updateEditableField('font_scale', scale.value)"
            class="px-2 py-2 rounded-lg border text-center transition-all"
            :class="(store.editableData?.font_scale || 'default') === scale.value
              ? 'border-cyan-500 bg-cyan-500/10 text-cyan-300'
              : 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-white'"
          >
            <span class="block text-xs font-medium">{{ scale.label }}</span>
            <span class="block text-[10px] text-gray-500 mt-0.5">{{ scale.preview }}</span>
          </button>
        </div>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()

interface Theme {
  name: string
  primary: string
  secondary: string
  fontHeading: string
  fontBody: string
}

const themes: Theme[] = [
  { name: 'Ocean', primary: '#2563EB', secondary: '#0EA5E9', fontHeading: 'Inter', fontBody: 'Inter' },
  { name: 'Forest', primary: '#059669', secondary: '#10B981', fontHeading: 'Lora', fontBody: 'Source Sans Pro' },
  { name: 'Sunset', primary: '#DC2626', secondary: '#F59E0B', fontHeading: 'Montserrat', fontBody: 'Open Sans' },
  { name: 'Royal', primary: '#7C3AED', secondary: '#A855F7', fontHeading: 'Playfair Display', fontBody: 'Lato' },
  { name: 'Slate', primary: '#334155', secondary: '#64748B', fontHeading: 'Space Grotesk', fontBody: 'DM Sans' },
  { name: 'Coral', primary: '#F43F5E', secondary: '#FB923C', fontHeading: 'Poppins', fontBody: 'Nunito' },
  { name: 'Teal', primary: '#0D9488', secondary: '#2DD4BF', fontHeading: 'Manrope', fontBody: 'Inter' },
  { name: 'Gold', primary: '#B45309', secondary: '#D97706', fontHeading: 'Merriweather', fontBody: 'Work Sans' },
  { name: 'Navy', primary: '#1E3A5F', secondary: '#2563EB', fontHeading: 'Raleway', fontBody: 'Roboto' },
  { name: 'Rose', primary: '#BE185D', secondary: '#EC4899', fontHeading: 'Outfit', fontBody: 'Sora' },
  { name: 'Olive', primary: '#4D7C0F', secondary: '#84CC16', fontHeading: 'Crimson Text', fontBody: 'Rubik' },
  { name: 'Midnight', primary: '#1E1B4B', secondary: '#4338CA', fontHeading: 'Space Grotesk', fontBody: 'Inter' },
]

function applyTheme(theme: Theme) {
  store.updateEditableField('color_primary', theme.primary)
  store.updateEditableField('color_secondary', theme.secondary)
  store.updateEditableField('font_heading', theme.fontHeading)
  store.updateEditableField('font_body', theme.fontBody)
}

function isActiveTheme(theme: Theme): boolean {
  const d = store.editableData
  if (!d) return false
  return d.color_primary === theme.primary
    && d.color_secondary === theme.secondary
    && d.font_heading === theme.fontHeading
    && d.font_body === theme.fontBody
}

const fontScales = [
  { value: 'compact', label: 'Compact', preview: '14px base' },
  { value: 'default', label: 'Default', preview: '16px base' },
  { value: 'large', label: 'Large', preview: '18px base' },
]

const fonts = [
  'Inter', 'Montserrat', 'Poppins', 'Raleway', 'Playfair Display',
  'Lato', 'Open Sans', 'Roboto', 'Source Sans Pro', 'Nunito',
  'DM Sans', 'Outfit', 'Space Grotesk', 'Sora', 'Manrope',
  'Merriweather', 'Lora', 'Crimson Text', 'Work Sans', 'Rubik',
]
</script>
