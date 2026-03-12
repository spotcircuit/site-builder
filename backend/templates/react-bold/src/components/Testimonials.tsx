import { useScrollAnimation } from '../hooks/useScrollAnimation'

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={filled ? 'text-primary' : 'text-gray-700'}
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

  if (!data.testimonials || data.testimonials.length === 0) return null

  return (
    <section
      id="testimonials"
      ref={sectionRef}
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-4xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            What Our Clients Say
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        {/* Stacked vertical testimonials - one at a time, large */}
        <div className="space-y-12">
          {data.testimonials.map((testimonial: any, index: number) => (
            <div
              key={index}
              className="bg-gray-800 border-l-4 border-primary p-10 md:p-14 relative"
            >
              {/* Large decorative quote mark in primary color */}
              <div className="absolute top-6 right-8 text-8xl font-serif text-primary/30 leading-none select-none pointer-events-none" aria-hidden="true">
                &rdquo;
              </div>

              {/* Star rating */}
              <div className="mb-6">
                <StarRating rating={testimonial.rating || 5} />
              </div>

              {/* Large testimonial text */}
              <blockquote className="text-white text-xl md:text-2xl font-medium leading-relaxed mb-8 relative">
                <span className="text-primary text-4xl font-serif leading-none mr-2">&ldquo;</span>
                {testimonial.text}
                <span className="text-primary text-4xl font-serif leading-none ml-2">&rdquo;</span>
              </blockquote>

              {/* Bold attribution */}
              <div className="border-t border-gray-700 pt-6 flex items-center justify-between">
                <div>
                  <p className="font-bold text-lg text-white font-heading uppercase tracking-wide">
                    {testimonial.author}
                  </p>
                  {testimonial.time && (
                    <p className="text-sm text-gray-500 mt-1">{testimonial.time}</p>
                  )}
                </div>
                {testimonial.verified && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.403 12.652a3 3 0 010-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.883l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                    </svg>
                    Google Review
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
