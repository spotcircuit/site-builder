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
      className="bg-white py-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            Why Choose Us
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-2 gap-12 items-center" : ""}>
          {/* Image side (left) */}
          {sectionImage && (
            <div className="rounded-2xl overflow-hidden shadow-xl">
              <img
                src={sectionImage}
                alt="Why choose us"
                className="w-full aspect-[16/10] object-cover"
              />
            </div>
          )}

          {/* Differentiators */}
          <div className={sectionImage ? "" : "max-w-5xl mx-auto"}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {data.why_choose_us.map((item: any, index: number) => (
                <div key={index} className="flex flex-row items-start gap-5">
                  {/* Circular icon container */}
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {getIcon(item.icon_key, 'w-7 h-7 text-primary')}
                  </div>

                  {/* Text content */}
                  <div>
                    <h3 className="font-semibold text-lg mb-2">
                      {item.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed">
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
