import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function FAQ({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.faq_items || data.faq_items.length === 0) {
    return null
  }

  return (
    <section
      ref={sectionRef}
      className="bg-gray-50 py-20 px-4"
    >
      <div className="max-w-3xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            Frequently Asked Questions
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        {/* Inline style for chevron rotation on open details */}
        <style>{`
          details[open] summary .chevron {
            transform: rotate(180deg);
          }
          details summary::-webkit-details-marker {
            display: none;
          }
          details summary::marker {
            display: none;
            content: '';
          }
        `}</style>

        {/* FAQ accordion */}
        <div>
          {data.faq_items.map((item: any, index: number) => (
            <details
              key={index}
              className={`border-b border-gray-200 ${
                index === data.faq_items.length - 1 ? 'border-0' : ''
              }`}
            >
              <summary className="py-5 px-2 cursor-pointer font-semibold text-lg text-gray-800 hover:text-primary transition-colors list-none flex justify-between items-center">
                <span>{item.question}</span>
                <svg
                  className="chevron w-5 h-5 text-gray-500 flex-shrink-0 ml-4 transition-transform duration-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="pb-5 px-2 text-gray-600 leading-relaxed">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}
