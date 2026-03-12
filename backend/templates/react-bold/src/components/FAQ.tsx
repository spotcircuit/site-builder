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
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-3xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            Frequently Asked Questions
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        {/* Inline style for chevron rotation on open details */}
        <style>{`
          details[open] summary .chevron {
            transform: rotate(180deg);
          }
          details[open] {
            border-left-width: 4px;
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
              className={`border-l-0 border-l-primary transition-all duration-200 ${
                index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-850 bg-gray-800/70'
              }`}
            >
              <summary className="py-6 px-6 cursor-pointer font-bold text-lg text-white hover:text-primary transition-colors list-none flex justify-between items-center">
                <span>{item.question}</span>
                <svg
                  className="chevron w-5 h-5 text-primary flex-shrink-0 ml-4 transition-transform duration-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="pb-6 px-6 text-gray-400 leading-relaxed">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}
