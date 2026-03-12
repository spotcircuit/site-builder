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

  const gradientFallback: Record<string, string> = {
    background: `linear-gradient(135deg, var(--tw-color-primary, ${data.color_primary || '#2563EB'}) 0%, var(--tw-color-secondary, ${data.color_secondary || '#7C3AED'}) 100%)`,
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
          <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/60 to-black/70" />
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

      {/* ── Decorative Circles ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-[1]" aria-hidden="true">
        <div
          className="absolute -top-20 -left-20 w-80 h-80 rounded-full opacity-[0.07]"
          style={{ background: data.color_secondary || '#F59E0B' }}
        />
        <div
          className="absolute top-1/3 right-0 w-64 h-64 rounded-full opacity-[0.05]"
          style={{ background: '#ffffff' }}
        />
        <div
          className="absolute -bottom-16 left-1/3 w-96 h-96 rounded-full opacity-[0.06]"
          style={{ background: data.color_primary || '#2563EB' }}
        />
        <div
          className="absolute top-10 right-1/4 w-40 h-40 rounded-full opacity-[0.04]"
          style={{ background: '#ffffff' }}
        />
      </div>

      {/* ── Content ── */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-28 md:py-40 text-center">
        <div className="animate-fade-in-up">
          <h1
            className="text-4xl md:text-5xl lg:text-6xl font-bold font-heading text-white
                       leading-[1.1] tracking-tight mb-6 max-w-4xl mx-auto"
          >
            {data.hero_headline || 'Welcome to Our Business'}
          </h1>

          <p
            className="text-xl md:text-2xl text-white/90 max-w-2xl mx-auto mb-10
                       leading-relaxed font-light"
          >
            {data.hero_subheadline || 'Professional services you can trust.'}
          </p>

          <a
            href="#contact"
            className="inline-flex items-center gap-2 bg-white px-8 py-4 rounded-xl
                       text-lg font-semibold shadow-lg
                       hover:shadow-xl hover:scale-[1.02]
                       active:scale-[0.98]
                       transition-all duration-300 ease-out"
            style={{ color: data.color_primary || '#2563EB' }}
          >
            {data.cta_button_text || 'Get Started'}
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              viewBox="0 0 24 24"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>

      {/* ── Bottom Gradient Fade ── */}
      <div
        className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(249, 250, 251, 0.08), transparent)',
        }}
      />
    </section>
  )
}
