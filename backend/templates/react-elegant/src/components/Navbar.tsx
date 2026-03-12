import { useState } from 'react'

interface NavbarProps {
  data: any
}

export default function Navbar({ data }: NavbarProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  const navLinks = [
    { label: 'About', href: '#about' },
    { label: 'Services', href: '#services' },
    { label: 'Testimonials', href: '#testimonials' },
    { label: 'Contact', href: '#contact' },
  ]

  const logoUrl = data.website_logo_url || data.website_data?.logo_url || data.logo_url

  return (
    <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* ── Brand ── */}
          <a
            href="#"
            className="flex items-center gap-2 text-xl font-heading text-gray-900 tracking-tight
                       hover:opacity-70 transition-opacity duration-200"
          >
            {logoUrl && (
              <img src={logoUrl} alt={data.business_name || data.name} className="h-7 w-auto" />
            )}
            {data.business_name || data.name || 'Our Business'}
          </a>

          {/* ── Desktop Links ── */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-xs font-medium text-gray-500 uppercase tracking-[0.15em]
                           hover:text-gray-900 transition-colors duration-200"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* ── Desktop CTA ── */}
          <a
            href="#contact"
            className="hidden md:inline-flex items-center px-6 py-2 text-xs font-medium
                       uppercase tracking-[0.15em] border border-gray-900 text-gray-900
                       hover:bg-gray-900 hover:text-white
                       transition-all duration-200 ease-out"
          >
            {data.cta_button_text || 'Get Started'}
          </a>

          {/* ── Mobile Hamburger ── */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden relative w-10 h-10 flex items-center justify-center
                       text-gray-500 hover:text-gray-900
                       transition-colors duration-200"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              viewBox="0 0 24 24"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {menuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="4" y1="7" x2="20" y2="7" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="17" x2="20" y2="17" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* ── Mobile Dropdown ── */}
      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
          menuOpen ? 'max-h-80 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-6 pt-2 space-y-1 border-t border-gray-100 bg-white">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-[0.15em]
                         hover:text-gray-900
                         transition-colors duration-200"
            >
              {link.label}
            </a>
          ))}
          <a
            href="#contact"
            onClick={() => setMenuOpen(false)}
            className="block w-full text-center mt-3 px-5 py-3 border border-gray-900
                       text-xs font-medium uppercase tracking-[0.15em] text-gray-900
                       hover:bg-gray-900 hover:text-white
                       transition-all duration-200"
          >
            {data.cta_button_text || 'Get Started'}
          </a>
        </div>
      </div>
    </nav>
  )
}
