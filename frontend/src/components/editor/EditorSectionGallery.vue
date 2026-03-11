<template>
  <EditorAccordion title="Images & Gallery" icon="I" sectionId="gallery">
    <div class="space-y-4">
      <!-- Hero Image -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Hero Background Image</label>
        <div class="flex gap-2">
          <input
            :value="store.editableData?.ai_hero_image || store.editableData?.website_hero_image || ''"
            @input="store.updateEditableField('ai_hero_image', ($event.target as HTMLInputElement).value)"
            class="flex-1 px-2 py-1.5 rounded bg-gray-800 border border-gray-600 text-white text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500 min-w-0"
            placeholder="Paste image URL..."
          />
          <label class="px-2 py-1.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30 text-xs cursor-pointer transition-colors flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Upload
            <input type="file" accept="image/*" class="hidden" @change="uploadHeroImage" />
          </label>
          <button
            v-if="store.editableData?.ai_hero_image"
            @click="store.updateEditableField('ai_hero_image', '')"
            class="px-2 py-1.5 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30 text-xs"
          >Clear</button>
        </div>
      </div>

      <!-- Logo -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Logo</label>
        <div class="flex gap-2">
          <input
            :value="store.editableData?.website_logo_url || store.editableData?.logo_url || ''"
            @input="store.updateEditableField('website_logo_url', ($event.target as HTMLInputElement).value)"
            class="flex-1 px-2 py-1.5 rounded bg-gray-800 border border-gray-600 text-white text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500 min-w-0"
            placeholder="Paste logo URL..."
          />
          <label class="px-2 py-1.5 rounded bg-cyan-600/20 text-cyan-300 hover:bg-cyan-600/30 text-xs cursor-pointer transition-colors flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Upload
            <input type="file" accept="image/*" class="hidden" @change="uploadLogo" />
          </label>
          <button
            v-if="store.editableData?.website_logo_url"
            @click="store.updateEditableField('website_logo_url', '')"
            class="px-2 py-1.5 rounded bg-red-600/20 text-red-400 hover:bg-red-600/30 text-xs"
          >Clear</button>
        </div>
      </div>

      <!-- Gallery Images -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="text-xs font-medium text-gray-400">Gallery Photos</label>
          <span class="text-xs text-gray-500">{{ images.length }} images</span>
        </div>

        <div class="space-y-2">
          <div
            v-for="(img, i) in images"
            :key="i"
            class="flex items-center gap-2 bg-gray-800/50 rounded-lg p-2 group"
          >
            <!-- Thumbnail -->
            <div class="w-10 h-10 rounded bg-gray-700 flex-shrink-0 overflow-hidden">
              <img
                v-if="getImageUrl(img)"
                :src="getImageUrl(img)"
                class="w-full h-full object-cover"
                @error="($event.target as HTMLImageElement).style.display = 'none'"
              />
            </div>

            <!-- URL input -->
            <input
              :value="getImageUrl(img)"
              @input="updateImage(i, ($event.target as HTMLInputElement).value)"
              class="flex-1 px-2 py-1 rounded bg-gray-700 border border-gray-600 text-white text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500 min-w-0"
              placeholder="Image URL..."
            />

            <!-- Move/Delete buttons -->
            <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
              <button
                v-if="i > 0"
                @click="store.moveEditableArrayItem(imageArrayKey, i, 'up')"
                class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
                title="Move up"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
              </button>
              <button
                v-if="i < images.length - 1"
                @click="store.moveEditableArrayItem(imageArrayKey, i, 'down')"
                class="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-700"
                title="Move down"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </button>
              <button
                @click="store.removeEditableArrayItem(imageArrayKey, i)"
                class="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-gray-700"
                title="Remove"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Add image buttons -->
        <div class="flex gap-2 mt-2">
          <button
            @click="addImage"
            class="flex-1 py-2 rounded-lg border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-cyan-500 text-xs transition-colors"
          >+ Add URL</button>
          <label class="flex-1 py-2 rounded-lg bg-cyan-600/20 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-600/30 text-xs transition-colors cursor-pointer text-center flex items-center justify-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Upload Images
            <input type="file" accept="image/*" multiple class="hidden" @change="uploadGalleryImages" />
          </label>
        </div>

        <!-- Upload progress -->
        <p v-if="uploading" class="text-xs text-cyan-400 mt-1 flex items-center gap-1">
          <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Uploading...
        </p>
      </div>
    </div>
  </EditorAccordion>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSiteBuilderStore } from '../../stores/siteBuilderStore'
import { uploadImage } from '../../services/api'
import EditorAccordion from './EditorAccordion.vue'

const store = useSiteBuilderStore()
const uploading = ref(false)

const imageArrayKey = computed(() => {
  if (!store.editableData) return 'photos'
  if (store.editableData.photos?.length > 0) return 'photos'
  if (store.editableData.website_images?.length > 0) return 'website_images'
  if (store.editableData.ai_gallery_images?.length > 0) return 'ai_gallery_images'
  return 'photos'
})

const images = computed(() => {
  if (!store.editableData) return []
  return store.editableData[imageArrayKey.value] || []
})

function getImageUrl(img: any): string {
  if (typeof img === 'string') return img
  return img?.url || img?.src || ''
}

function updateImage(index: number, url: string) {
  const img = images.value[index]
  if (typeof img === 'string') {
    store.updateEditableField(`${imageArrayKey.value}.${index}`, url)
  } else {
    store.updateEditableField(`${imageArrayKey.value}.${index}.url`, url)
  }
}

function addImage() {
  const key = imageArrayKey.value
  if (!store.editableData) return
  if (!store.editableData[key]) store.editableData[key] = []
  const sample = images.value[0]
  if (typeof sample === 'string' || images.value.length === 0) {
    store.editableData[key].push('')
  } else {
    store.editableData[key].push({ url: '', alt: '' })
  }
}

async function uploadHeroImage(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const result = await uploadImage(file)
    store.updateEditableField('ai_hero_image', result.url)
  } catch (err: any) {
    store.editorError = err.message || 'Upload failed'
  } finally {
    uploading.value = false;
    (e.target as HTMLInputElement).value = ''
  }
}

async function uploadLogo(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const result = await uploadImage(file)
    store.updateEditableField('website_logo_url', result.url)
  } catch (err: any) {
    store.editorError = err.message || 'Upload failed'
  } finally {
    uploading.value = false;
    (e.target as HTMLInputElement).value = ''
  }
}

async function uploadGalleryImages(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || files.length === 0) return
  uploading.value = true
  const key = imageArrayKey.value
  if (!store.editableData) return
  if (!store.editableData[key]) store.editableData[key] = []

  try {
    for (const file of Array.from(files)) {
      const result = await uploadImage(file)
      const sample = images.value[0]
      if (typeof sample === 'string' || images.value.length === 0) {
        store.editableData[key].push(result.url)
      } else {
        store.editableData[key].push({ url: result.url, alt: file.name })
      }
    }
  } catch (err: any) {
    store.editorError = err.message || 'Upload failed'
  } finally {
    uploading.value = false;
    (e.target as HTMLInputElement).value = ''
  }
}
</script>
