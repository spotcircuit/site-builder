import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function HowItWorks({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.process_steps || data.process_steps.length === 0) return null

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      className="bg-gray-50 py-20 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            How It Works
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        {/* Steps timeline */}
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-none md:flex md:items-start gap-4 md:gap-0">
            {data.process_steps.map((step: any, index: number) => (
              <div key={index} className="flex md:flex-col items-start md:items-center flex-1 relative">
                {/* Connecting line (desktop only) */}
                {index < data.process_steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-7 left-[calc(50%+28px)] right-0 h-0.5 bg-gradient-to-r from-primary/30 to-primary/10"
                    style={{ width: 'calc(100% - 28px)' }}
                  />
                )}

                {/* Connecting line (mobile only) */}
                {index < data.process_steps.length - 1 && (
                  <div className="block md:hidden absolute top-14 left-7 w-0.5 h-[calc(100%-14px)] bg-gradient-to-b from-primary/30 to-primary/10" />
                )}

                {/* Step number circle */}
                <div className="relative z-10 w-14 h-14 rounded-full bg-primary text-white flex items-center justify-center text-xl font-bold shadow-lg shadow-primary/25 flex-shrink-0">
                  {step.step_number || index + 1}
                </div>

                {/* Step content */}
                <div className="ml-5 md:ml-0 md:mt-6 md:text-center md:px-3 pb-8 md:pb-0">
                  {/* Icon */}
                  {step.icon_key && (
                    <div className="hidden md:flex w-10 h-10 rounded-lg bg-primary/10 items-center justify-center mx-auto mb-3">
                      {getIcon(step.icon_key, 'w-5 h-5 text-primary')}
                    </div>
                  )}

                  <h3 className="text-lg font-semibold font-heading text-gray-900 mb-2">
                    {step.title}
                  </h3>

                  <p className="text-gray-600 text-sm leading-relaxed max-w-[220px] md:max-w-none">
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
