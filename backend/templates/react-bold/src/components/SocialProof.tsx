import { useScrollAnimation } from '../hooks/useScrollAnimation'

interface SocialProofProps {
  data: any
}

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      className={`w-5 h-5 ${filled ? 'text-primary' : 'text-gray-700'}`}
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
      className="relative bg-gray-950 border-t-2 border-primary"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
          {/* -- Star Rating with primary color stars -- */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon key={star} filled={star <= fullStars} />
              ))}
            </div>
            <span className="text-lg font-black text-white tabular-nums">
              {rating.toFixed(1)}
            </span>
          </div>

          {/* -- Divider -- */}
          {reviewCount > 0 && (
            <div className="hidden sm:block w-px h-5 bg-gray-700" aria-hidden="true" />
          )}

          {/* -- Review Count - bold numbers -- */}
          {reviewCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black text-white tabular-nums">
                {reviewCount.toLocaleString()}
              </span>
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                reviews
              </span>
            </div>
          )}

          {/* -- Divider -- */}
          {category && (
            <div className="hidden sm:block w-px h-5 bg-gray-700" aria-hidden="true" />
          )}

          {/* -- Category Pill -- */}
          {category && (
            <span
              className="inline-flex items-center px-4 py-1 text-xs font-bold uppercase tracking-widest
                         bg-primary/10 text-primary border border-primary/30"
            >
              {category}
            </span>
          )}
        </div>
      </div>
    </section>
  )
}
