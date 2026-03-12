<template>
  <div>
    <label v-if="label" class="block text-xs font-medium text-gray-400 mb-1.5">{{ label }}</label>
    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      :rows="rows"
      class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm leading-relaxed focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-y placeholder-gray-500"
      :placeholder="placeholder"
    />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  modelValue: string
  label?: string
  rows?: number
  placeholder?: string
}>(), {
  rows: 4,
  placeholder: '',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
