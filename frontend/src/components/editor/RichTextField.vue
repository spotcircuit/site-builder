<template>
  <div>
    <label v-if="label" class="block text-xs font-medium text-gray-400 mb-1.5">{{ label }}</label>
    <div class="rounded border border-gray-600 overflow-hidden rich-text-wrapper">
      <Editor
        :init="editorConfig"
        :modelValue="modelValue"
        @update:modelValue="$emit('update:modelValue', $event)"
        api-key="no-api-key"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Editor from '@tinymce/tinymce-vue'

const props = withDefaults(defineProps<{
  modelValue: string
  label?: string
  rows?: number
}>(), {
  rows: 4,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorConfig = {
  height: props.rows * 40 + 60,
  menubar: false,
  skin: 'oxide-dark',
  content_css: 'dark',
  plugins: 'lists link autolink',
  toolbar: 'bold italic underline | bullist numlist | link | removeformat',
  toolbar_location: 'bottom' as const,
  statusbar: false,
  branding: false,
  promotion: false,
  content_style: `
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 13px;
      line-height: 1.5;
      padding: 8px;
      margin: 0;
    }
    p { margin: 0 0 0.5em 0; }
  `,
}
</script>

<style>
.rich-text-wrapper .tox-tinymce {
  border: none !important;
}
</style>
