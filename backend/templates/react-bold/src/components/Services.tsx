import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function Services({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const sectionImage = data.ai_services_image || null

  return (
    <section
      id="services"
      ref={sectionRef}
      className="bg-gray-50 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold font-heading text-gray-900 mb-4">
            Our Services
          </h2>
          <div className="w-24 h-1.5 bg-primary rounded-full" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-5 gap-10 items-start" : ""}>
          {/* Services list */}
          <div className={sectionImage ? "lg:col-span-3" : ""}>
            <div className="grid grid-cols-1 gap-6">
              {data.services?.map((service: any, index: number) => (
                <div
                  key={index}
                  className="bg-white border-l-4 border-primary shadow-sm hover:shadow-lg
                             transition-all duration-300 p-8 md:p-10
                             hover:translate-x-1"
                >
                  <div className="flex items-start gap-6">
                    {/* Icon container */}
                    <div className="w-16 h-16 rounded-none bg-primary/10 flex items-center justify-center flex-shrink-0">
                      {getIcon(service.icon_suggestion, 'w-9 h-9 text-primary')}
                    </div>

                    <div>
                      {/* Service name */}
                      <h3 className="text-xl md:text-2xl font-bold font-heading mb-3">
                        {service.name}
                      </h3>

                      {/* Service description */}
                      <p className="text-gray-600 leading-relaxed text-lg">
                        {service.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section image */}
          {sectionImage && (
            <div className="lg:col-span-2 hidden lg:block">
              <div className="overflow-hidden shadow-xl sticky top-24 border-4 border-primary">
                <img
                  src={sectionImage}
                  alt="Our services"
                  className="w-full aspect-[16/9] object-cover"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
