import { useScrollAnimation } from '../hooks/useScrollAnimation'

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={filled ? 'text-yellow-400' : 'text-gray-200'}
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
      className="bg-white py-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            What Our Clients Say
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        {/* Testimonials grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {data.testimonials.map((testimonial: any, index: number) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 p-8 border border-gray-100 relative"
            >
              {/* Decorative opening quote */}
              <div className="absolute top-4 right-6 text-6xl font-serif text-primary/10 leading-none select-none pointer-events-none" aria-hidden="true">
                &rdquo;
              </div>

              {/* Star rating */}
              <div className="mb-5">
                <StarRating rating={testimonial.rating || 5} />
              </div>

              {/* Testimonial text */}
              <blockquote className="text-gray-700 italic leading-relaxed mb-6 relative">
                <span className="text-primary/40 text-2xl font-serif leading-none mr-1">&ldquo;</span>
                {testimonial.text}
                <span className="text-primary/40 text-2xl font-serif leading-none ml-1">&rdquo;</span>
              </blockquote>

              {/* Author */}
              <div className="border-t border-gray-100 pt-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900 font-heading">
                    {testimonial.author}
                  </p>
                  {testimonial.time && (
                    <p className="text-xs text-gray-400 mt-0.5">{testimonial.time}</p>
                  )}
                </div>
                {testimonial.verified && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 text-xs font-medium">
                    <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
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
