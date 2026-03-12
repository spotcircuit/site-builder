import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function WhyChooseUs({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const sectionImage = data.ai_why_choose_us_image || null

  if (!data.why_choose_us || data.why_choose_us.length === 0) {
    return null
  }

  return (
    <section
      id="why-choose-us"
      ref={sectionRef}
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            Why Choose Us
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-2 gap-12 items-center" : ""}>
          {/* Image side (left) */}
          {sectionImage && (
            <div className="overflow-hidden border-2 border-primary">
              <img
                src={sectionImage}
                alt="Why choose us"
                className="w-full aspect-[16/10] object-cover"
              />
            </div>
          )}

          {/* Differentiators - stacked layout */}
          <div className={sectionImage ? "" : "max-w-5xl mx-auto"}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {data.why_choose_us.map((item: any, index: number) => (
                <div key={index} className="flex flex-col items-start gap-4 bg-gray-800 p-6 border-l-4 border-primary">
                  {/* Large icon area with primary color */}
                  <div className="w-16 h-16 bg-primary/15 flex items-center justify-center flex-shrink-0">
                    {getIcon(item.icon_key, 'w-8 h-8 text-primary')}
                  </div>

                  {/* Text content */}
                  <div>
                    <h3 className="font-bold text-xl text-white mb-2 uppercase tracking-wide">
                      {item.title}
                    </h3>
                    <p className="text-gray-400 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
