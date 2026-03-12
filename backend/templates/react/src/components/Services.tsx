import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function Services({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const sectionImage = data.ai_services_image || null

  return (
    <section
      id="services"
      ref={sectionRef}
      className="bg-gray-50 py-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            Our Services
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        <div className={sectionImage ? "grid grid-cols-1 lg:grid-cols-5 gap-10 items-start" : ""}>
          {/* Services grid */}
          <div className={sectionImage ? "lg:col-span-3" : ""}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {data.services?.map((service: any, index: number) => (
                <div
                  key={index}
                  className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-8 hover:transform hover:-translate-y-1"
                >
                  {/* Icon container */}
                  <div className="w-14 h-14 rounded-lg bg-primary/10 flex items-center justify-center mb-5">
                    {getIcon(service.icon_suggestion, 'w-8 h-8 text-primary')}
                  </div>

                  {/* Service name */}
                  <h3 className="text-xl font-semibold font-heading mb-3">
                    {service.name}
                  </h3>

                  {/* Service description */}
                  <p className="text-gray-600 leading-relaxed">
                    {service.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Section image */}
          {sectionImage && (
            <div className="lg:col-span-2 hidden lg:block">
              <div className="rounded-2xl overflow-hidden shadow-xl sticky top-24">
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
