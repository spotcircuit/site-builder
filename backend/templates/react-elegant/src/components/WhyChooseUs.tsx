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
      className="bg-stone-50/50 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            Why Choose Us
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-2 gap-16 items-center" : ""}>
          {/* Image side (left) */}
          {sectionImage && (
            <div className="rounded-lg overflow-hidden">
              <img
                src={sectionImage}
                alt="Why choose us"
                className="w-full h-96 object-cover"
              />
            </div>
          )}

          {/* Differentiators */}
          <div className={sectionImage ? "" : "max-w-4xl mx-auto"}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
              {data.why_choose_us.map((item: any, index: number) => (
                <div
                  key={index}
                  className="border-t border-gray-200 py-8 px-6 text-center"
                >
                  {/* Icon */}
                  <div className="mb-4 text-primary/70 flex justify-center">
                    {getIcon(item.icon_key, 'w-6 h-6')}
                  </div>

                  {/* Title */}
                  <h3 className="font-heading text-base tracking-tight mb-2 text-gray-900">
                    {item.title}
                  </h3>

                  {/* Description */}
                  <p className="text-gray-500 leading-relaxed text-sm">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
