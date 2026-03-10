import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function WhyChooseUs({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.why_choose_us || data.why_choose_us.length === 0) {
    return null
  }

  return (
    <section
      ref={sectionRef}
      className="bg-white py-20 px-4"
    >
      <div className="max-w-5xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            Why Choose Us
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        {/* Differentiators grid */}
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
    </section>
  )
}
