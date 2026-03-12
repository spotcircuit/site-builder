import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function CTA({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  return (
    <section
      id="cta"
      ref={sectionRef}
      className="relative py-24 md:py-32 px-4 overflow-hidden"
      style={{
        backgroundColor: data.color_primary || '#2563eb',
      }}
    >
      {/* Subtle diagonal stripe overlay for texture */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 20px, rgba(255,255,255,0.1) 20px, rgba(255,255,255,0.1) 22px)',
        }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto text-center">
        <h2 className="text-4xl md:text-5xl lg:text-6xl font-black font-heading mb-10 text-white uppercase tracking-tight leading-tight">
          {data.cta_headline}
        </h2>

        <a
          href="#contact"
          className="inline-block bg-white px-12 py-5 text-lg font-black uppercase tracking-widest shadow-2xl hover:shadow-none transition-all duration-300 hover:bg-gray-100"
          style={{ color: data.color_primary || '#2563eb' }}
        >
          {data.cta_button_text}
        </a>
      </div>
    </section>
  )
}
