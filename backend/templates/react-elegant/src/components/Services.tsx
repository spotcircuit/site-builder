import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function Services({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const sectionImage = data.ai_services_image || null

  return (
    <section
      id="services"
      ref={sectionRef}
      className="bg-white py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            Our Services
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-5 gap-10 items-start" : ""}>
          {/* Services grid */}
          <div className={sectionImage ? "lg:col-span-3" : ""}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0">
              {data.services?.map((service: any, index: number) => (
                <div
                  key={index}
                  className="border-t border-gray-200 pt-8 pb-10 px-6
                             hover:bg-gray-50/50 transition-colors duration-300"
                >
                  {/* Icon */}
                  <div className="mb-5 text-primary/70">
                    {getIcon(service.icon_suggestion, 'w-7 h-7')}
                  </div>

                  {/* Service name */}
                  <h3 className="text-lg font-heading tracking-tight mb-3 text-gray-900">
                    {service.name}
                  </h3>

                  {/* Service description */}
                  <p className="text-gray-500 leading-relaxed text-sm">
                    {service.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Section image */}
          {sectionImage && (
            <div className="lg:col-span-2 hidden lg:block">
              <div className="rounded-lg overflow-hidden sticky top-24">
                <img
                  src={sectionImage}
                  alt="Our services"
                  className="w-full h-auto object-cover"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
