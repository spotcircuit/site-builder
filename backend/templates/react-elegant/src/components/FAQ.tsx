import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function FAQ({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.faq_items || data.faq_items.length === 0) {
    return null
  }

  return (
    <section
      id="faq"
      ref={sectionRef}
      className="bg-white py-24 px-4"
    >
      <div className="max-w-2xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            Frequently Asked Questions
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
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
              className="border-b border-gray-100"
            >
              <summary className="py-6 cursor-pointer font-medium text-gray-800 hover:text-primary transition-colors list-none flex justify-between items-center">
                <span className="text-base">{item.question}</span>
                <svg
                  className="chevron w-4 h-4 text-gray-400 flex-shrink-0 ml-4 transition-transform duration-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="pb-6 text-gray-500 leading-relaxed text-sm">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}
