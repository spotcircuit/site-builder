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
      className="py-24 px-4 bg-stone-50/50"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-heading tracking-tight text-gray-900 mb-4">
            Gallery
          </h2>
          <div className="w-10 h-px bg-primary mx-auto" />
        </div>

        {/* Photo grid — masonry-inspired with varying heights */}
        <div className="columns-1 sm:columns-2 lg:columns-3 gap-4 space-y-4">
          {photos.map((photo: string, index: number) => (
            <div
              key={index}
              className="break-inside-avoid overflow-hidden rounded-lg group"
            >
              <img
                src={photo}
                alt={`${data.business_name || 'Business'} photo ${index + 1}`}
                loading="lazy"
                className="w-full h-auto object-cover group-hover:scale-[1.02] transition-transform duration-700 ease-out"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
