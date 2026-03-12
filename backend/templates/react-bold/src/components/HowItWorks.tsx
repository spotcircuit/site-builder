import { useScrollAnimation } from '../hooks/useScrollAnimation'
import { getIcon } from '../icons/heroicons'

export default function HowItWorks({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  if (!data.process_steps || data.process_steps.length === 0) return null

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            How It Works
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        {/* Steps timeline */}
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-none md:flex md:items-start gap-4 md:gap-0">
            {data.process_steps.map((step: any, index: number) => (
              <div key={index} className="flex md:flex-col items-start md:items-center flex-1 relative">
                {/* Bold connecting line (desktop only) */}
                {index < data.process_steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-8 left-[calc(50%+32px)] right-0 h-1 bg-primary/40"
                    style={{ width: 'calc(100% - 32px)' }}
                  />
                )}

                {/* Bold connecting line (mobile only) */}
                {index < data.process_steps.length - 1 && (
                  <div className="block md:hidden absolute top-16 left-8 w-1 h-[calc(100%-16px)] bg-primary/40" />
                )}

                {/* Large step number - square, dramatic */}
                <div className="relative z-10 w-16 h-16 bg-primary text-white flex items-center justify-center text-2xl font-black shadow-lg shadow-primary/30 flex-shrink-0">
                  {step.step_number || index + 1}
                </div>

                {/* Step content - sharp card styling */}
                <div className="ml-6 md:ml-0 md:mt-6 md:text-center md:px-3 pb-10 md:pb-0">
                  {/* Icon */}
                  {step.icon_key && (
                    <div className="hidden md:flex w-12 h-12 bg-primary/10 items-center justify-center mx-auto mb-3 border border-primary/20">
                      {getIcon(step.icon_key, 'w-6 h-6 text-primary')}
                    </div>
                  )}

                  <h3 className="text-lg font-bold font-heading text-white mb-2 uppercase tracking-wide">
                    {step.title}
                  </h3>

                  <p className="text-gray-400 text-sm leading-relaxed max-w-[220px] md:max-w-none">
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
