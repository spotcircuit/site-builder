import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function CTA({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  return (
    <section
      id="cta"
      ref={sectionRef}
      className="relative py-24 px-4 bg-white border-t border-b border-gray-100"
    >
      {/* Content */}
      <div className="relative z-10 max-w-2xl mx-auto text-center">
        <div className="w-10 h-px bg-primary mx-auto mb-10" />

        <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-10">
          {data.cta_headline}
        </h2>

        <a
          href="#contact"
          className="inline-flex items-center px-10 py-4 text-sm font-medium
                     uppercase tracking-[0.2em] border
                     transition-all duration-300 ease-out
                     hover:bg-primary hover:text-white"
          style={{
            borderColor: data.color_primary || '#2563eb',
            color: data.color_primary || '#2563eb',
          }}
        >
          {data.cta_button_text}
        </a>
      </div>
    </section>
  )
}
