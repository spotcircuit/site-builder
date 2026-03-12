function parseVideoUrl(url: string): { type: 'youtube' | 'vimeo' | null; id: string } {
  if (!url) return { type: null, id: '' }
  const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
  if (ytMatch) return { type: 'youtube', id: ytMatch[1] }
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/)
  if (vimeoMatch) return { type: 'vimeo', id: vimeoMatch[1] }
  return { type: null, id: '' }
}

interface HeroProps {
  data: any
}

export default function Hero({ data }: HeroProps) {
  const hasPhoto = data.photos && data.photos.length > 0
  const firstPhoto = hasPhoto ? data.photos[0] : null
  const websiteHeroImage = data.website_hero_image || null
  const aiHeroImage = data.ai_hero_image || null

  // Priority: Google Maps photo > website hero image > AI-generated image > gradient fallback
  const heroImage = firstPhoto || websiteHeroImage || aiHeroImage
  const video = parseVideoUrl(data.hero_video_url || '')

  const gradientFallback: React.CSSProperties = {
    background: `linear-gradient(160deg, #fafaf9 0%, #f5f0eb 50%, #faf5ef 100%)`,
  }

  return (
    <section id="hero" className="relative overflow-hidden min-h-[500px] md:min-h-[600px]" style={!heroImage && !video.type ? gradientFallback : undefined}>
      {/* ── Hero Background Image ── */}
      {heroImage && !video.type && (
        <>
          <img
            src={heroImage}
            alt=""
            className="absolute inset-0 w-full h-full object-cover object-center"
            loading="eager"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-white/55 via-white/60 to-white/70" />
        </>
      )}

      {/* ── Video Background ── */}
      {video.type && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <iframe
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ width: '177.78vh', minWidth: '100%', minHeight: '100%', border: 'none' }}
            src={video.type === 'youtube'
              ? `https://www.youtube-nocookie.com/embed/${video.id}?autoplay=1&mute=1&loop=1&playlist=${video.id}&controls=0&showinfo=0&rel=0&modestbranding=1&playsinline=1`
              : `https://player.vimeo.com/video/${video.id}?autoplay=1&muted=1&loop=1&background=1`}
            allow="autoplay; fullscreen"
            loading="lazy"
            title="Hero background video"
          />
          <div className="absolute inset-0 bg-black/50" />
        </div>
      )}

      {/* ── Content ── */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-36 md:py-52 text-center">
        <div className="animate-fade-in-up">
          {/* Thin decorative rule */}
          <div
            className="w-12 h-px mx-auto mb-10"
            style={{ backgroundColor: data.color_primary || '#2563EB' }}
          />

          <h1
            className="text-4xl md:text-6xl font-heading tracking-tight text-gray-900
                       leading-[1.1] mb-8 max-w-3xl mx-auto"
          >
            {data.hero_headline || 'Welcome to Our Business'}
          </h1>

          <p
            className="text-lg text-gray-500 max-w-xl mx-auto mb-12
                       leading-relaxed tracking-wide"
          >
            {data.hero_subheadline || 'Professional services you can trust.'}
          </p>

          <a
            href="#contact"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-none
                       text-sm font-medium uppercase tracking-[0.2em]
                       border transition-all duration-300 ease-out
                       hover:bg-primary hover:text-white"
            style={{
              borderColor: data.color_primary || '#2563EB',
              color: data.color_primary || '#2563EB',
            }}
          >
            {data.cta_button_text || 'Get Started'}
          </a>
        </div>
      </div>
    </section>
  )
}
