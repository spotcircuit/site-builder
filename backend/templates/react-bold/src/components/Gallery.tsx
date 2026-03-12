import { useScrollAnimation } from '../hooks/useScrollAnimation'

export default function Gallery({ data }: { data: any }) {
  const sectionRef = useScrollAnimation()

  // Priority: Google Maps photos > website-scraped images > AI-generated gallery images
  const photos = (data.photos && data.photos.length > 0)
    ? data.photos
    : (data.website_images && data.website_images.length > 0)
      ? data.website_images
      : (data.ai_gallery_images || [])

  if (photos.length === 0) return null

  return (
    <section
      id="gallery"
      ref={sectionRef}
      className="bg-gray-900 py-24 px-4"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black font-heading text-white mb-4 uppercase tracking-tight">
            Gallery
          </h2>
          <div className="w-24 h-1.5 bg-primary mx-auto" />
        </div>

        {/* Photo grid - no rounding, tight gaps, hover border */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {photos.map((photo: string, index: number) => (
            <div
              key={index}
              className="overflow-hidden group cursor-pointer border-2 border-transparent hover:border-primary transition-all duration-300"
            >
              <div className="overflow-hidden">
                <img
                  src={photo}
                  alt={`${data.business_name || 'Business'} photo ${index + 1}`}
                  loading="lazy"
                  className="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
