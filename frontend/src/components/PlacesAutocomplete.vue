<template>
  <div class="relative">
    <label for="business-search" class="block text-sm font-medium text-gray-300 mb-2">
      Find a Business
    </label>
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        id="business-search"
        ref="inputRef"
        v-model="inputValue"
        type="text"
        :placeholder="autocompleteReady
          ? 'Search for any business...'
          : 'Paste a Google Maps URL...'"
        class="w-full pl-12 pr-12 py-3.5 rounded-xl bg-gray-900/50 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-base transition-all"
        :disabled="disabled"
        autocomplete="off"
        @keydown.enter="handleEnter"
      />
      <button
        v-if="inputValue"
        @click="clearInput"
        class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-gray-300 transition-colors"
        type="button"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Selected business pill -->
    <div
      v-if="selectedPlace"
      class="mt-3 flex items-center gap-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg px-4 py-2.5"
    >
      <svg class="w-5 h-5 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-white truncate">{{ selectedPlace.name }}</p>
        <p class="text-xs text-gray-400 truncate">{{ selectedPlace.address }}</p>
      </div>
      <button
        @click="clearSelection"
        class="text-gray-500 hover:text-gray-300 transition-colors flex-shrink-0"
        type="button"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Helper text -->
    <p class="mt-2 text-xs text-gray-500">
      <template v-if="autocompleteReady">
        Type a business name to search, or paste a Google Maps URL
      </template>
      <template v-else>
        Paste a full Google Maps URL (autocomplete unavailable — no API key)
      </template>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { ensureGoogleMapsLoaded } from '../services/mapsLoader'

interface SelectedPlace {
  name: string
  address: string
  placeId: string | null
  mapsUrl: string
}

const emit = defineEmits<{
  (e: 'select', place: SelectedPlace): void
  (e: 'clear'): void
}>()

const props = defineProps<{
  disabled?: boolean
  modelValue?: string
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref(props.modelValue || '')
const autocompleteReady = ref(false)
const selectedPlace = ref<SelectedPlace | null>(null)

let autocompleteInstance: any = null

onMounted(async () => {
  try {
    await ensureGoogleMapsLoaded()
    await nextTick()
    attachAutocomplete()
  } catch (err) {
    console.warn('[PlacesAutocomplete] Google Maps not available:', err)
  }
})

function attachAutocomplete() {
  if (!inputRef.value) return
  const google = (window as any).google
  if (!google?.maps?.places) return

  autocompleteInstance = new google.maps.places.Autocomplete(inputRef.value, {
    types: ['establishment'],
    fields: ['name', 'formatted_address', 'place_id', 'geometry'],
  })

  autocompleteInstance.addListener('place_changed', () => {
    const place = autocompleteInstance.getPlace()
    if (!place || !place.name) return

    const name = place.name
    const address = place.formatted_address || ''
    const placeId = place.place_id || null

    // Build a Maps search URL that the backend scraper can handle
    const searchQuery = encodeURIComponent(`${name} ${address}`)
    const mapsUrl = `https://www.google.com/maps/search/${searchQuery}`

    const selected: SelectedPlace = { name, address, placeId, mapsUrl }
    selectedPlace.value = selected
    inputValue.value = `${name}, ${address}`

    emit('select', selected)
  })

  autocompleteReady.value = true
}

function handleEnter() {
  // If input looks like a Maps URL, treat it as a direct URL paste
  const val = inputValue.value.trim()
  if (isGoogleMapsUrl(val)) {
    const selected: SelectedPlace = {
      name: 'From URL',
      address: val,
      placeId: null,
      mapsUrl: val,
    }
    selectedPlace.value = selected
    emit('select', selected)
  }
}

function isGoogleMapsUrl(val: string): boolean {
  return /google\.\w+\/maps|maps\.app\.goo\.gl|goo\.gl\/maps/i.test(val)
}

function clearInput() {
  inputValue.value = ''
  selectedPlace.value = null
  emit('clear')
  inputRef.value?.focus()
}

function clearSelection() {
  selectedPlace.value = null
  inputValue.value = ''
  emit('clear')
  inputRef.value?.focus()
}

// Sync with parent model
watch(() => props.modelValue, (val) => {
  if (val !== undefined) inputValue.value = val
})
</script>
