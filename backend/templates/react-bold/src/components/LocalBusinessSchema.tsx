/** Maps day name strings to Schema.org dayOfWeek values. */
const DAY_MAP: Record<string, string> = {
  monday: 'https://schema.org/Monday',
  tuesday: 'https://schema.org/Tuesday',
  wednesday: 'https://schema.org/Wednesday',
  thursday: 'https://schema.org/Thursday',
  friday: 'https://schema.org/Friday',
  saturday: 'https://schema.org/Saturday',
  sunday: 'https://schema.org/Sunday',
}

/**
 * Parse a time string like "9:00 AM - 10:00 PM" into 24h opens/closes values.
 * Returns null if the format cannot be parsed.
 */
function parseTimeRange(timeStr: string): { opens: string; closes: string } | null {
  const parts = timeStr.split(/\s*[-\u2013]\s*/)
  if (parts.length !== 2) return null

  const to24h = (t: string): string | null => {
    const match = t.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i)
    if (!match) return null
    let hours = parseInt(match[1], 10)
    const minutes = match[2]
    const period = match[3].toUpperCase()
    if (period === 'PM' && hours !== 12) hours += 12
    if (period === 'AM' && hours === 12) hours = 0
    return `${String(hours).padStart(2, '0')}:${minutes}`
  }

  const opens = to24h(parts[0])
  const closes = to24h(parts[1])
  if (!opens || !closes) return null
  return { opens, closes }
}

/**
 * Renders a JSON-LD structured data script tag for Schema.org LocalBusiness markup.
 * Produces no visible DOM output -- only a <script type="application/ld+json"> tag.
 */
export default function LocalBusinessSchema({ data }: { data: any }) {
  const schema: Record<string, any> = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
  }

  if (data.business_name) schema.name = data.business_name
  if (data.seo_description) schema.description = data.seo_description
  if (data.phone) schema.telephone = data.phone
  if (data.website) schema.url = data.website

  // Use the first available image
  if (data.ai_hero_image) {
    schema.image = data.ai_hero_image
  } else if (data.photos && data.photos.length > 0) {
    schema.image = data.photos[0]
  }

  // additionalType from category (e.g. "Pizza Restaurant")
  if (data.category) schema.additionalType = data.category

  // PostalAddress from the combined address string
  if (data.address) {
    schema.address = {
      '@type': 'PostalAddress',
      streetAddress: data.address,
    }
  }

  // GeoCoordinates
  if (data.latitude != null && data.longitude != null) {
    schema.geo = {
      '@type': 'GeoCoordinates',
      latitude: data.latitude,
      longitude: data.longitude,
    }
  }

  // openingHoursSpecification from data.hours (dict of day -> time range)
  if (data.hours && typeof data.hours === 'object' && !Array.isArray(data.hours)) {
    const specs: Record<string, any>[] = []
    for (const [day, timeStr] of Object.entries(data.hours)) {
      const dayUrl = DAY_MAP[day.toLowerCase()]
      if (!dayUrl) continue
      const parsed = parseTimeRange(timeStr as string)
      if (!parsed) continue
      specs.push({
        '@type': 'OpeningHoursSpecification',
        dayOfWeek: dayUrl,
        opens: parsed.opens,
        closes: parsed.closes,
      })
    }
    if (specs.length > 0) {
      schema.openingHoursSpecification = specs
    }
  }

  // AggregateRating
  if (data.rating != null) {
    const aggregateRating: Record<string, any> = {
      '@type': 'AggregateRating',
      ratingValue: data.rating,
      bestRating: 5,
    }
    if (data.review_count != null) {
      aggregateRating.reviewCount = data.review_count
    }
    schema.aggregateRating = aggregateRating
  }

  // Individual reviews
  if (Array.isArray(data.reviews) && data.reviews.length > 0) {
    schema.review = data.reviews
      .filter((r: any) => r && (r.author || r.rating || r.text))
      .map((r: any) => {
        const review: Record<string, any> = { '@type': 'Review' }
        if (r.author) {
          review.author = { '@type': 'Person', name: r.author }
        }
        if (r.rating != null) {
          review.reviewRating = {
            '@type': 'Rating',
            ratingValue: r.rating,
            bestRating: 5,
          }
        }
        if (r.text) {
          review.reviewBody = r.text
        }
        return review
      })
    if (schema.review.length === 0) {
      delete schema.review
    }
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema, null, 2) }}
    />
  )
}
