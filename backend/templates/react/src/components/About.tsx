import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function About({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const aboutImage = data.ai_about_image || (data.photos && data.photos.length > 1 ? data.photos[1] : null)

  return (
    <section
      id="about"
      ref={sectionRef}
      className="bg-white py-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        <div className={aboutImage ? "grid grid-cols-1 md:grid-cols-2 gap-12 items-center" : "max-w-4xl mx-auto text-center"}>
          {/* Text side */}
          <div>
            <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
              {data.about_title}
            </h2>
            <div className={`w-20 h-1 bg-primary rounded-full mb-8 ${!aboutImage ? 'mx-auto' : ''}`} />
            <p className="text-lg text-gray-600 leading-relaxed">
              {data.about_text}
            </p>
          </div>

          {/* Image side */}
          {aboutImage && (
            <div className="rounded-2xl overflow-hidden shadow-xl">
              <img
                src={aboutImage}
                alt={data.about_title || 'About us'}
                className="w-full aspect-[4/3] object-cover"
              />
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
