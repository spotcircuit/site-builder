import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function HowItWorks({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.process_steps || data.process_steps.length === 0) return null

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      className="bg-white py-28 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            How It Works
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
        </div>

        {/* Steps timeline */}
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-none md:flex md:items-start gap-4 md:gap-0">
            {data.process_steps.map((step: any, index: number) => (
              <div key={index} className="flex md:flex-col items-start md:items-center flex-1 relative">
                {/* Connecting line (desktop only) */}
                {index < data.process_steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-6 left-[calc(50%+24px)] right-0 h-px bg-gray-200"
                    style={{ width: 'calc(100% - 24px)' }}
                  />
                )}

                {/* Connecting line (mobile only) */}
                {index < data.process_steps.length - 1 && (
                  <div className="block md:hidden absolute top-12 left-6 w-px h-[calc(100%-12px)] bg-gray-200" />
                )}

                {/* Step number circle — refined thin border */}
                <div
                  className="relative z-10 w-12 h-12 rounded-full border flex items-center justify-center
                             text-sm font-heading flex-shrink-0 bg-white"
                  style={{
                    borderColor: data.color_primary || '#2563EB',
                    color: data.color_primary || '#2563EB',
                  }}
                >
                  {step.step_number || index + 1}
                </div>

                {/* Step content */}
                <div className="ml-5 md:ml-0 md:mt-8 md:text-center md:px-3 pb-10 md:pb-0">
                  {/* Icon */}
                  {step.icon_key && (
                    <div className="hidden md:flex w-8 h-8 items-center justify-center mx-auto mb-3 text-primary/60">
                      {getIcon(step.icon_key, 'w-5 h-5')}
                    </div>
                  )}

                  <h3 className="text-base font-heading tracking-tight text-gray-900 mb-2">
                    {step.title}
                  </h3>

                  <p className="text-gray-500 text-sm leading-relaxed max-w-[220px] md:max-w-none">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
