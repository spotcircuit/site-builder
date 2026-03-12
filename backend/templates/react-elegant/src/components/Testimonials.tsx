import { useState } from 'react'
import { useScrollAnimation } from '../hooks/useScrollAnimation'

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={filled ? 'text-primary/60' : 'text-gray-200'}
    >
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  )
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <StarIcon key={star} filled={star <= rating} />
      ))}
    </div>
  )
}

export default function Testimonials({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const [activeIndex, setActiveIndex] = useState(0)

  if (!data.testimonials || data.testimonials.length === 0) return null

  const testimonial = data.testimonials[activeIndex]

  return (
    <section
      id="testimonials"
      ref={sectionRef}
      className="bg-white py-28 px-4"
    >
      <div className="max-w-3xl mx-auto text-center">
        {/* Section heading */}
        <div className="mb-16">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            What Our Clients Say
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
        </div>

        {/* Large decorative quotation mark */}
        <div
          className="text-8xl font-serif leading-none mb-6 select-none"
          style={{ color: data.color_primary || '#2563EB', opacity: 0.15 }}
          aria-hidden="true"
        >
          &ldquo;
        </div>

        {/* Star rating */}
        <div className="flex justify-center mb-8">
          <StarRating rating={testimonial.rating || 5} />
        </div>

        {/* Testimonial text */}
        <blockquote className="text-xl md:text-2xl text-gray-600 italic leading-relaxed mb-10 font-heading">
          {testimonial.text}
        </blockquote>

        {/* Author */}
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-gray-900">
            {testimonial.author}
          </p>
          {testimonial.time && (
            <p className="text-xs text-gray-400 mt-2">{testimonial.time}</p>
          )}
          {testimonial.verified && (
            <span className="inline-flex items-center gap-1 mt-3 text-xs text-gray-400">
              <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.403 12.652a3 3 0 010-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.883l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
              </svg>
              Verified Review
            </span>
          )}
        </div>

        {/* Dot navigation */}
        {data.testimonials.length > 1 && (
          <div className="flex justify-center gap-3 mt-12">
            {data.testimonials.map((_: any, index: number) => (
              <button
                key={index}
                onClick={() => setActiveIndex(index)}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === activeIndex
                    ? 'bg-primary w-6'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
                aria-label={`View testimonial ${index + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
