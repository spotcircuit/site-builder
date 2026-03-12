import { useState } from 'react'
import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function Contact({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
  }

  const contactImage = data.ai_contact_image || null

  return (
    <section
      id="contact"
      ref={sectionRef}
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-5xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            Get In Touch
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        {/* Contact banner image */}
        {contactImage && (
          <div className="overflow-hidden mb-12">
            <img
              src={contactImage}
              alt="Visit us"
              className="w-full h-64 object-cover"
            />
          </div>
        )}

        {/* Two-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* LEFT COLUMN - Contact info */}
          <div className="space-y-6">
            {/* Phone */}
            {data.phone && (
              <a
                href={`tel:${data.phone}`}
                className="flex items-start gap-4 text-gray-400 hover:text-primary transition-colors group"
              >
                <div className="w-12 h-12 bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                  </svg>
                </div>
                <div>
                  <p className="font-bold text-white mb-1 uppercase text-sm tracking-wide">Phone</p>
                  <p>{data.phone}</p>
                </div>
              </a>
            )}

            {/* Email */}
            {data.email && (
              <a
                href={`mailto:${data.email}`}
                className="flex items-start gap-4 text-gray-400 hover:text-primary transition-colors group"
              >
                <div className="w-12 h-12 bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                  </svg>
                </div>
                <div>
                  <p className="font-bold text-white mb-1 uppercase text-sm tracking-wide">Email</p>
                  <p>{data.email}</p>
                </div>
              </a>
            )}

            {/* Address */}
            {data.address && (
              <div className="flex items-start gap-4 text-gray-400">
                <div className="w-12 h-12 bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                </div>
                <div>
                  <p className="font-bold text-white mb-1 uppercase text-sm tracking-wide">Address</p>
                  <p>{data.address}</p>
                </div>
              </div>
            )}

            {/* Hours */}
            {data.hours && (
              <div className="flex items-start gap-4 text-gray-400">
                <div className="w-12 h-12 bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="font-bold text-white mb-1 uppercase text-sm tracking-wide">Business Hours</p>
                  {Array.isArray(data.hours) ? (
                    data.hours.map((hour: string, index: number) => (
                      <p key={index}>{hour}</p>
                    ))
                  ) : typeof data.hours === 'object' ? (
                    Object.entries(data.hours).map(([day, time]) => (
                      <p key={day}>
                        <span className="font-medium capitalize">{day}:</span> {time as string}
                      </p>
                    ))
                  ) : (
                    <p>{String(data.hours)}</p>
                  )}
                </div>
              </div>
            )}

            {/* Google Maps embed */}
            {(data.business_name || data.latitude) && (
              <iframe
                src={`https://www.google.com/maps?q=${encodeURIComponent(data.business_name + (data.address ? ' ' + data.address : ''))}&z=17&output=embed`}
                width="100%"
                height="250"
                style={{ border: 0 }}
                allowFullScreen
                loading="lazy"
                className="mt-6"
                title="Business location"
              />
            )}
          </div>

          {/* RIGHT COLUMN - Contact form */}
          <div className="bg-gray-800 p-8">
            <h3 className="text-xl font-black font-heading text-primary mb-6 uppercase tracking-wide">
              Send Us a Message
            </h3>

            {submitted ? (
              <div className="text-center py-12 space-y-3">
                <div className="w-16 h-16 bg-primary/20 flex items-center justify-center mx-auto">
                  <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-lg font-bold text-white">Thank you!</p>
                <p className="text-gray-400">We'll get back to you soon.</p>
                <button
                  onClick={() => setSubmitted(false)}
                  className="mt-4 text-sm text-primary hover:underline font-bold uppercase tracking-wide"
                >
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <input
                    type="text"
                    placeholder="Your Name"
                    required
                    className="w-full px-4 py-3 rounded-none border border-gray-700 bg-gray-900 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition"
                  />
                </div>

                <div>
                  <input
                    type="email"
                    placeholder="Your Email"
                    required
                    className="w-full px-4 py-3 rounded-none border border-gray-700 bg-gray-900 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition"
                  />
                </div>

                <div>
                  <input
                    type="tel"
                    placeholder="Your Phone"
                    className="w-full px-4 py-3 rounded-none border border-gray-700 bg-gray-900 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition"
                  />
                </div>

                <div>
                  <textarea
                    placeholder="Your Message"
                    rows={4}
                    required
                    className="w-full px-4 py-3 rounded-none border border-gray-700 bg-gray-900 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition resize-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-4 rounded-none text-white font-black uppercase tracking-widest hover:opacity-90 transition text-lg"
                  style={{ backgroundColor: data.color_primary || '#2563eb' }}
                >
                  Send Message
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
