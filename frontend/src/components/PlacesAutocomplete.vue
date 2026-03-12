<template>
  <div class="relative">
    <label for="business-search" class="block text-sm font-medium text-gray-300 mb-2">
      Business name, Google Maps link, or website URL
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
          ? 'Search a business name or paste any URL...'
          : 'Paste a Google Maps link or website URL...'"
        class="w-full pl-12 pr-12 py-3.5 rounded-xl bg-gray-900/50 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent text-base transition-all"
        :disabled="disabled"
        autocomplete="off"
        @keydown.enter="handleEnter"
        @input="handleInput"
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

    <!-- Selected business pill (Maps) -->
    <div
      v-if="selectedPlace"
      class="mt-3 space-y-2"
    >
      <div class="flex items-center gap-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg px-4 py-2.5">
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
      <!-- Data badges for Maps -->
      <div class="flex flex-wrap gap-2 pl-1">
        <span class="inline-flex items-center gap-1 text-[11px] text-cyan-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          Photos
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-cyan-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
          Reviews
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-cyan-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
          Contact
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-cyan-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Hours
        </span>
      </div>
    </div>

    <!-- Website URL detected pill -->
    <div
      v-if="detectedType === 'website' && !selectedPlace"
      class="mt-3 space-y-2"
    >
      <div class="flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-2.5">
        <svg class="w-5 h-5 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-white">Website found</p>
          <p class="text-xs text-gray-400 truncate">{{ inputValue }}</p>
        </div>
      </div>
      <!-- Data badges for Website -->
      <div class="flex flex-wrap gap-2 pl-1">
        <span class="inline-flex items-center gap-1 text-[11px] text-emerald-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>
          Colors
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-emerald-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          Images
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-emerald-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          Content
        </span>
        <span class="inline-flex items-center gap-1 text-[11px] text-emerald-300/70">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
          Social Links
        </span>
      </div>
    </div>

    <!-- Helper text (only when nothing detected yet) -->
    <p v-if="!selectedPlace && detectedType === 'none'" class="mt-2 text-xs text-gray-500">
      <template v-if="autocompleteReady">
        Search by name, or paste a Google Maps link or any website URL
      </template>
      <template v-else>
        Paste a Google Maps link or any business website URL
      </template>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { ensureGoogleMapsLoaded } from '../services/mapsLoader'

interface SelectedPlace {
  name: string
  address: string
  placeId: string | null
  mapsUrl: string
}

const emit = defineEmits<{
  (e: 'select', place: SelectedPlace): void
  (e: 'website-url', url: string): void
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

const detectedType = computed(() => {
  const val = inputValue.value.trim()
  if (!val) return 'none'
  if (isGoogleMapsUrl(val)) return 'maps'
  if (/^https?:\/\//i.test(val)) return 'website'
  return 'none'
})

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

function handleInput() {
  const val = inputValue.value.trim()

  // Auto-detect URL type on paste/input
  if (isGoogleMapsUrl(val)) {
    const selected: SelectedPlace = {
      name: 'From URL',
      address: val,
      placeId: null,
      mapsUrl: val,
    }
    selectedPlace.value = selected
    emit('select', selected)
  } else if (/^https?:\/\//i.test(val) && val.includes('.')) {
    // It's a website URL — emit website-url event
    selectedPlace.value = null
    emit('website-url', val)
  } else {
    // Not a URL — could be a search query for autocomplete
    if (!isGoogleMapsUrl(val) && !/^https?:\/\//i.test(val)) {
      selectedPlace.value = null
    }
  }
}

function handleEnter() {
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
  } else if (/^https?:\/\//i.test(val)) {
    emit('website-url', val)
  }
}

function isGoogleMapsUrl(val: string): boolean {
  return /google\.[^/]+\/maps|maps\.app\.goo\.gl|goo\.gl\/maps/i.test(val)
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
