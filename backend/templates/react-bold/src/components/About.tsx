import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function About({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const aboutImage = data.ai_about_image || (data.photos && data.photos.length > 1 ? data.photos[1] : null)

  return (
    <section
      id="about"
      ref={sectionRef}
      className="bg-white py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        <div className={aboutImage ? "grid grid-cols-1 md:grid-cols-2 gap-16 items-center" : "max-w-4xl mx-auto"}>
          {/* Text side - large quote style */}
          <div>
            <div className="w-24 h-1.5 bg-primary rounded-full mb-8" />
            <h2 className="text-4xl md:text-5xl font-bold font-heading text-gray-900 mb-6 leading-tight">
              {data.about_title}
            </h2>
            <div className="border-l-4 border-primary pl-6">
              <p className="text-xl text-gray-600 leading-relaxed">
                {data.about_text}
              </p>
            </div>
          </div>

          {/* Image side with bold colored border/frame */}
          {aboutImage && (
            <div className="relative">
              {/* Offset colored frame behind the image */}
              <div
                className="absolute -bottom-4 -right-4 w-full h-full"
                style={{ background: data.color_primary || '#2563EB' }}
              />
              <div className="relative overflow-hidden shadow-xl">
                <img
                  src={aboutImage}
                  alt={data.about_title || 'About us'}
                  className="w-full h-96 object-cover"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
