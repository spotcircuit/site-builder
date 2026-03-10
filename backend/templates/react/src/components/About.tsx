import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function About({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  return (
    <section
      id="about"
      ref={sectionRef}
      className="bg-white py-20 px-4"
    >
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
          {data.about_title}
        </h2>

        {/* Decorative accent line */}
        <div className="w-20 h-1 bg-primary mx-auto mb-8 rounded-full" />

        <p className="text-lg text-gray-600 leading-relaxed max-w-3xl mx-auto">
          {data.about_text}
        </p>
      </div>
    </section>
  )
}
