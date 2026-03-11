import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function CTA({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  return (
    <section
      id="cta"
      ref={sectionRef}
      className="relative py-20 px-4 overflow-hidden"
      style={{
        background: `linear-gradient(135deg, ${data.color_primary || '#2563eb'}, ${data.color_secondary || '#7c3aed'})`,
      }}
    >
      {/* Decorative blurred circles for depth */}
      <div
        className="absolute top-[-80px] left-[-80px] w-64 h-64 rounded-full opacity-20 blur-3xl"
        style={{ backgroundColor: '#ffffff' }}
      />
      <div
        className="absolute bottom-[-60px] right-[-60px] w-80 h-80 rounded-full opacity-15 blur-3xl"
        style={{ backgroundColor: '#ffffff' }}
      />
      <div
        className="absolute top-1/2 left-1/3 w-48 h-48 rounded-full opacity-10 blur-2xl"
        style={{ backgroundColor: '#ffffff' }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-3xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold font-heading mb-8 text-white">
          {data.cta_headline}
        </h2>

        <a
          href="#contact"
          className="inline-block bg-white px-10 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-0.5"
          style={{ color: data.color_primary || '#2563eb' }}
        >
          {data.cta_button_text}
        </a>
      </div>
    </section>
  )
}
