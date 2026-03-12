import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function About({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const aboutImage = data.ai_about_image || (data.photos && data.photos.length > 1 ? data.photos[1] : null)

  return (
    <section
      id="about"
      ref={sectionRef}
      className="bg-stone-50/50 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        <div className={aboutImage ? "grid grid-cols-1 md:grid-cols-2 gap-16 items-center" : "max-w-3xl mx-auto text-center"}>
          {/* Text side */}
          <div>
            {/* Thin accent line */}
            <div className={`w-10 h-px bg-primary mb-6 ${!aboutImage ? 'mx-auto' : ''}`} />

            <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-6">
              {data.about_title}
            </h2>

            <p className="text-lg text-gray-500 leading-8">
              {data.about_text}
            </p>
          </div>

          {/* Image side */}
          {aboutImage && (
            <div className="rounded-lg overflow-hidden">
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
