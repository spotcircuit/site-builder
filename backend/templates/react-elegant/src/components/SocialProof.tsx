import { useScrollAnimation } from '../hooks/useScrollAnimation'

interface SocialProofProps {
  data: any
}

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      className={`w-3.5 h-3.5 ${filled ? 'text-primary/60' : 'text-gray-300'}`}
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden="true"
    >
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  )
}

export default function SocialProof({ data }: SocialProofProps) {
  const ref = useScrollAnimation(0.1)

  if (!data.rating) return null

  const rating = parseFloat(data.rating) || 0
  const fullStars = Math.floor(rating)
  const reviewCount = data.review_count || 0
  const category = data.category || null

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className="bg-white border-b border-gray-100"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
          {/* ── Star Rating ── */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon key={star} filled={star <= fullStars} />
              ))}
            </div>
            <span className="text-xs font-medium text-gray-600 tabular-nums">
              {rating.toFixed(1)}
            </span>
          </div>

          {/* ── Divider ── */}
          {reviewCount > 0 && (
            <div className="hidden sm:block w-px h-3 bg-gray-200" aria-hidden="true" />
          )}

          {/* ── Review Count ── */}
          {reviewCount > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500">
                <span className="font-medium text-gray-700">{reviewCount.toLocaleString()}</span>
                {' '}reviews
              </span>
            </div>
          )}

          {/* ── Divider ── */}
          {category && (
            <div className="hidden sm:block w-px h-3 bg-gray-200" aria-hidden="true" />
          )}

          {/* ── Category ── */}
          {category && (
            <span className="text-xs text-gray-500 tracking-wide">
              {category}
            </span>
          )}
        </div>
      </div>
    </section>
  )
}
