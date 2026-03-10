import { useScrollAnimation } from '../hooks/useScrollAnimation'

interface SocialProofProps {
  data: any
}

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      className={`w-4 h-4 ${filled ? 'text-yellow-400' : 'text-gray-500'}`}
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
      className="relative bg-gray-900/95 backdrop-blur-sm border-t border-white/5"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
          {/* ── Star Rating ── */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon key={star} filled={star <= fullStars} />
              ))}
            </div>
            <span className="text-sm font-semibold text-white tabular-nums">
              {rating.toFixed(1)}
            </span>
          </div>

          {/* ── Divider ── */}
          {reviewCount > 0 && (
            <div className="hidden sm:block w-px h-4 bg-white/20" aria-hidden="true" />
          )}

          {/* ── Review Count Badge ── */}
          {reviewCount > 0 && (
            <div className="flex items-center gap-1.5">
              <svg
                className="w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
                viewBox="0 0 24 24"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>
              <span className="text-sm text-gray-300">
                <span className="font-semibold text-white">{reviewCount.toLocaleString()}</span>
                {' '}reviews
              </span>
            </div>
          )}

          {/* ── Divider ── */}
          {category && (
            <div className="hidden sm:block w-px h-4 bg-white/20" aria-hidden="true" />
          )}

          {/* ── Category Pill ── */}
          {category && (
            <span
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
                         bg-white/10 text-gray-200 border border-white/10
                         backdrop-blur-sm"
            >
              {category}
            </span>
          )}
        </div>
      </div>
    </section>
  )
}
