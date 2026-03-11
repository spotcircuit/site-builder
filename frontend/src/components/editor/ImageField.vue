<template>
  <div>
    <label class="block text-xs font-medium text-gray-400 mb-1">{{ label }}</label>
    <div class="flex gap-2 items-center">
      <!-- Thumbnail -->
      <div v-if="modelValue" class="w-8 h-8 rounded bg-gray-700 flex-shrink-0 overflow-hidden">
        <img :src="modelValue" class="w-full h-full object-cover" @error="($event.target as HTMLImageElement).style.display = 'none'" />
      </div>
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        class="flex-1 px-2 py-1.5 rounded bg-gray-800 border border-gray-600 text-white text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500 min-w-0"
        placeholder="Paste image URL..."
      />
      <label class="px-2 py-1.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30 text-xs cursor-pointer transition-colors flex items-center gap-1 flex-shrink-0">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
        Upload
        <input type="file" accept="image/*" class="hidden" @change="handleUpload" />
      </label>
      <button
        v-if="modelValue"
        @click="$emit('update:modelValue', '')"
        class="p-1.5 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30 flex-shrink-0"
        title="Remove image"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>
    <p v-if="uploading" class="text-xs text-cyan-400 mt-1 flex items-center gap-1">
      <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Uploading...
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { uploadImage } from '../../services/api'

defineProps<{
  label: string
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const uploading = ref(false)

async function handleUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const result = await uploadImage(file)
    emit('update:modelValue', result.url)
  } catch (err: any) {
    console.error('Upload failed:', err)
  } finally {
    uploading.value = false;
    (e.target as HTMLInputElement).value = ''
  }
}
</script>
