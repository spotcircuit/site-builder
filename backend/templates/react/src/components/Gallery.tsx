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
      className="py-16 px-4"
      style={{ backgroundColor: 'rgba(var(--color-primary-rgb, 59, 130, 246), 0.05)' }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-primary mb-4">
            Gallery
          </h2>
          <div className="w-20 h-1 bg-primary mx-auto rounded-full" />
        </div>

        {/* Photo grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {photos.map((photo: string, index: number) => (
            <div
              key={index}
              className="overflow-hidden rounded-xl shadow-md group cursor-pointer"
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
