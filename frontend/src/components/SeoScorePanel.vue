<template>
  <div class="w-full max-w-[400px] bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6 space-y-5">
    <!-- Header -->
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <h3 class="text-sm font-semibold text-white uppercase tracking-wider">Local SEO Score</h3>
    </div>

    <!-- Score Gauge -->
    <div class="flex items-center gap-5">
      <div class="relative w-24 h-24 flex-shrink-0">
        <svg class="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="42"
            fill="none"
            stroke="currentColor"
            stroke-width="8"
            class="text-gray-700"
          />
          <circle
            cx="50" cy="50" r="42"
            fill="none"
            :stroke="scoreColor"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="dashOffset"
            class="transition-all duration-1000 ease-out"
          />
        </svg>
        <div class="absolute inset-0 flex flex-col items-center justify-center">
          <span class="text-2xl font-bold" :style="{ color: scoreColor }">{{ seoScore }}</span>
          <span class="text-[10px] text-gray-500 -mt-0.5">/ 100</span>
        </div>
      </div>
      <div>
        <p class="text-sm font-medium" :style="{ color: scoreColor }">{{ scoreLabel }}</p>
        <p class="text-xs text-gray-500 mt-0.5">{{ businessName }}</p>
      </div>
    </div>

    <!-- Checklist -->
    <div class="space-y-2">
      <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Ranking Signals</p>
      <div class="space-y-1.5">
        <div
          v-for="item in checklistItems"
          :key="item.label"
          class="flex items-center gap-2.5 text-sm"
        >
          <!-- Check icon -->
          <svg
            v-if="item.pass"
            class="w-4 h-4 text-emerald-400 flex-shrink-0"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <!-- X icon -->
          <svg
            v-else
            class="w-4 h-4 text-red-400 flex-shrink-0"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span :class="item.pass ? 'text-gray-300' : 'text-gray-500'">{{ item.label }}</span>
        </div>
      </div>
    </div>

    <!-- Improvement Suggestions -->
    <div v-if="suggestions.length > 0" class="space-y-2">
      <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Suggestions</p>
      <div class="space-y-1.5">
        <div
          v-for="(suggestion, i) in suggestions"
          :key="i"
          class="flex items-start gap-2 text-xs text-yellow-400/80"
        >
          <svg class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ suggestion }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  businessName: string
  rating: number | null
  reviewCount: number | null
  hasPhone: boolean
  hasAddress: boolean
  hasWebsite: boolean
  hasHours: boolean
  hasPhotos: boolean
  hasReviews: boolean
  category: string
  seoTitle: string
  seoDescription: string
}

const props = defineProps<Props>()

const circumference = 2 * Math.PI * 42

const seoScore = computed(() => {
  let score = 0

  // Business name: +10
  if (props.businessName) score += 10

  // Rating: +15 or +20
  if (props.rating !== null) {
    if (props.rating >= 4.5) score += 20
    else if (props.rating >= 4.0) score += 15
  }

  // Reviews: +10, +15, or +20
  if (props.reviewCount !== null) {
    if (props.reviewCount >= 500) score += 20
    else if (props.reviewCount >= 100) score += 15
    else if (props.reviewCount >= 50) score += 10
  }

  // NAP signals
  if (props.hasPhone) score += 10
  if (props.hasAddress) score += 10
  if (props.hasWebsite) score += 5

  // Business details
  if (props.hasHours) score += 5
  if (props.hasPhotos) score += 5
  if (props.hasReviews) score += 10

  // Category
  if (props.category) score += 5

  // SEO title under 60 chars
  if (props.seoTitle && props.seoTitle.length > 0 && props.seoTitle.length <= 60) score += 5

  // SEO description 120-160 chars
  const descLen = props.seoDescription?.length ?? 0
  if (descLen >= 120 && descLen <= 160) score += 5

  return Math.min(score, 100)
})

const dashOffset = computed(() => {
  return circumference - (seoScore.value / 100) * circumference
})

const scoreColor = computed(() => {
  if (seoScore.value > 80) return '#34d399'   // emerald-400
  if (seoScore.value >= 60) return '#fbbf24'  // yellow-400
  return '#f87171'                             // red-400
})

const scoreLabel = computed(() => {
  if (seoScore.value > 80) return 'Excellent'
  if (seoScore.value >= 60) return 'Good'
  return 'Needs Improvement'
})

const napConsistent = computed(() => props.hasPhone && props.hasAddress && !!props.businessName)

const ratingPass = computed(() => props.rating !== null && props.rating >= 4.0)
const reviewsPass = computed(() => props.reviewCount !== null && props.reviewCount >= 50)
const titleOptimized = computed(() => !!props.seoTitle && props.seoTitle.length > 0 && props.seoTitle.length <= 60)
const descOptimized = computed(() => {
  const len = props.seoDescription?.length ?? 0
  return len >= 120 && len <= 160
})

const checklistItems = computed(() => [
  {
    label: ratingPass.value
      ? `Google Rating: ${props.rating}/5`
      : 'Google Rating: Missing',
    pass: ratingPass.value,
  },
  {
    label: reviewsPass.value
      ? `Reviews: ${props.reviewCount}`
      : props.reviewCount !== null
        ? `Reviews: ${props.reviewCount} (need 50+)`
        : 'Reviews: Missing',
    pass: reviewsPass.value,
  },
  {
    label: 'NAP Consistent',
    pass: napConsistent.value,
  },
  {
    label: 'Business Hours Listed',
    pass: props.hasHours,
  },
  {
    label: 'Photos Available',
    pass: props.hasPhotos,
  },
  {
    label: 'Real Customer Reviews',
    pass: props.hasReviews,
  },
  {
    label: 'Business Category Set',
    pass: !!props.category,
  },
  {
    label: 'SEO Title Optimized',
    pass: titleOptimized.value,
  },
  {
    label: 'Meta Description Optimized',
    pass: descOptimized.value,
  },
])

const suggestions = computed(() => {
  const items: string[] = []

  if (!ratingPass.value && props.rating !== null && props.rating < 4.0) {
    items.push('Improve Google rating to 4.0+ to boost local search visibility.')
  }
  if (props.rating === null) {
    items.push('Claim and verify your Google Business Profile to get rated.')
  }
  if (!reviewsPass.value) {
    items.push('Add more Google reviews to improve local ranking.')
  }
  if (!napConsistent.value) {
    items.push('Ensure Name, Address, and Phone are all listed for NAP consistency.')
  }
  if (!props.hasHours) {
    items.push('List business hours to appear in local search results.')
  }
  if (!props.hasPhotos) {
    items.push('Upload photos to increase engagement and click-through rate.')
  }
  if (!props.hasReviews) {
    items.push('Encourage customers to leave reviews on your Google profile.')
  }
  if (!props.category) {
    items.push('Set a business category to help Google match relevant searches.')
  }
  if (!titleOptimized.value) {
    items.push('Keep your SEO title under 60 characters for optimal display in search results.')
  }
  if (!descOptimized.value) {
    items.push('Write a meta description between 120-160 characters for best SERP display.')
  }
  if (!props.hasWebsite) {
    items.push('Add a website link to your Google Business Profile.')
  }

  return items
})
</script>
