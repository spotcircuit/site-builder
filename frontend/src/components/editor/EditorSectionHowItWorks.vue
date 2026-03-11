<template>
  <EditorAccordion title="How It Works" icon="H" sectionId="how-it-works">
    <div class="space-y-3">
      <div
        v-for="(step, i) in steps"
        :key="i"
        class="bg-gray-800/50 rounded-lg p-3 space-y-2 relative group"
      >
        <div class="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button v-if="i > 0" @click="store.moveEditableArrayItem('process_steps', i, 'up'); renumber()" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move up">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button v-if="i < steps.length - 1" @click="store.moveEditableArrayItem('process_steps', i, 'down'); renumber()" class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Move down">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button @click="removeStep(i)" class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700" title="Remove">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400 font-mono whitespace-nowrap">Step {{ step.step_number }}</span>
          <input
            :value="step.title || ''"
            @input="store.updateEditableField(`process_steps.${i}.title`, ($event.target as HTMLInputElement).value)"
            class="flex-1 px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="Step title"
          />
        </div>
        <textarea
          :value="step.description || ''"
          @input="store.updateEditableField(`process_steps.${i}.description`, ($event.target as HTMLTextAreaElement).value)"
          rows="2"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none"
          placeholder="Description..."
        ></textarea>
        <input
          :value="step.icon_key || ''"
          @input="store.updateEditableField(`process_steps.${i}.icon_key`, ($event.target as HTMLInputElement).value)"
          class="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="Icon key (e.g. phone, calendar, check)"
        />
      </div>

      <div class="flex gap-2">
        <button
          @click="addStep()"
          class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-sm transition-colors"
        >+ Add Step</button>
        <button
          @click="$emit('generate', 'process_steps')"
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
const steps = computed(() => store.editableData?.process_steps || [])

function addStep() {
  const nextNumber = steps.value.length > 0
    ? Math.max(...steps.value.map((s: any) => s.step_number || 0)) + 1
    : 1
  store.addEditableArrayItem('process_steps', {
    step_number: nextNumber,
    title: '',
    description: '',
    icon_key: 'circle',
  })
}

function renumber() {
  const arr = store.editableData?.process_steps
  if (Array.isArray(arr)) {
    arr.forEach((step: any, i: number) => { step.step_number = i + 1 })
  }
}

function removeStep(index: number) {
  store.removeEditableArrayItem('process_steps', index)
  // Re-number remaining steps sequentially
  const arr = store.editableData?.process_steps
  if (Array.isArray(arr)) {
    arr.forEach((step: any, i: number) => {
      step.step_number = i + 1
    })
  }
}
</script>
