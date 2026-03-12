<template>
  <EditorAccordion title="Contact" icon="C" sectionId="contact">
    <div class="space-y-3">
      <!-- Multi-location / franchise warning -->
      <div
        v-if="store.editableData?.contact_confidence === 'low'"
        class="px-3 py-2.5 rounded-lg bg-amber-900/30 border border-amber-600/30 text-xs"
      >
        <div class="flex items-center gap-2 mb-1">
          <svg class="w-4 h-4 text-amber-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span class="font-semibold text-amber-300">Multiple locations detected</span>
        </div>
        <p class="text-amber-200/70 leading-relaxed">This appears to be a franchise or multi-location business. Please verify the address and phone number for your specific location.</p>
        <div v-if="locations.length > 0" class="mt-2 space-y-1">
          <p class="text-gray-400 text-[10px] font-medium uppercase tracking-wide">Click to use:</p>
          <button
            v-for="(loc, i) in locations"
            :key="i"
            class="block w-full text-left px-2 py-1 rounded text-[11px] text-gray-300 hover:bg-amber-800/30 hover:text-amber-200 transition-colors truncate"
            @click="store.updateEditableField('address', loc)"
          >
            {{ loc }}
          </button>
        </div>
      </div>

      <!-- No contact info found -->
      <div
        v-if="store.editableData?.contact_confidence === 'none'"
        class="px-3 py-2.5 rounded-lg bg-blue-900/30 border border-blue-600/30 text-xs"
      >
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-blue-200/70">No contact info found on the website. Please fill in your details below.</p>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Phone</label>
        <input
          :value="store.editableData?.phone || ''"
          @input="store.updateEditableField('phone', ($event.target as HTMLInputElement).value)"
          :class="[
            'w-full px-3 py-2 rounded-lg bg-gray-800 border text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500',
            needsVerification && !store.editableData?.phone ? 'border-amber-500/50' : 'border-gray-600'
          ]"
          placeholder="(555) 123-4567"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Address</label>
        <input
          :value="store.editableData?.address || ''"
          @input="store.updateEditableField('address', ($event.target as HTMLInputElement).value)"
          :class="[
            'w-full px-3 py-2 rounded-lg bg-gray-800 border text-white text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500',
            needsVerification && !store.editableData?.address ? 'border-amber-500/50' : 'border-gray-600'
          ]"
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
import { computed } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import EditorAccordion from './EditorAccordion.vue'
import ImageField from './ImageField.vue'

const store = useSiteBuilderStore()

const needsVerification = computed(() => {
  const confidence = store.editableData?.contact_confidence
  return confidence === 'low' || confidence === 'none'
})

const locations = computed(() => {
  return (store.editableData?.all_locations || []).slice(0, 8)
})
</script>
