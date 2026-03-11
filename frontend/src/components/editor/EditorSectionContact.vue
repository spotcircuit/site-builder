<template>
  <EditorAccordion title="Contact" icon="C" sectionId="contact">
    <div class="space-y-3">
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Phone</label>
        <input
          :value="store.editableData?.phone || ''"
          @input="store.updateEditableField('phone', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="(555) 123-4567"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Address</label>
        <input
          :value="store.editableData?.address || ''"
          @input="store.updateEditableField('address', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="123 Main St, City, ST 12345"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Email</label>
        <input
          :value="store.editableData?.email || ''"
          @input="store.updateEditableField('email', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="info@business.com"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Website</label>
        <input
          :value="store.editableData?.website || ''"
          @input="store.updateEditableField('website', ($event.target as HTMLInputElement).value)"
          class="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="https://example.com"
        />
      </div>
      <ImageField
        label="Contact Section Image"
        :modelValue="store.editableData?.ai_contact_image || ''"
        @update:modelValue="store.updateEditableField('ai_contact_image', $event)"
      />
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'
import ImageField from './ImageField.vue'
const store = useSiteBuilderStore()
</script>
