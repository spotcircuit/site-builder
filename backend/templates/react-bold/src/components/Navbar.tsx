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
    <nav className="sticky top-0 z-50 bg-gray-950 border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-18">
          {/* -- Brand -- */}
          <a
            href="#"
            className="flex items-center gap-2 text-2xl font-black font-heading text-white tracking-tight uppercase
                       hover:text-primary transition-colors duration-200"
          >
            {logoUrl && (
              <img src={logoUrl} alt={data.business_name || data.name} className="h-8 w-auto" />
            )}
            {data.business_name || data.name || 'Our Business'}
          </a>

          {/* -- Desktop Links -- */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="relative px-4 py-2 text-xs font-bold text-gray-400 uppercase tracking-widest
                           hover:text-primary transition-colors duration-200
                           after:absolute after:bottom-0 after:left-1/2 after:-translate-x-1/2
                           after:w-0 after:h-0.5 after:bg-primary
                           after:transition-all after:duration-300
                           hover:after:w-full"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* -- Desktop CTA -- */}
          <a
            href="#contact"
            className="hidden md:inline-flex items-center px-6 py-2.5 bg-primary text-white
                       text-xs font-black uppercase tracking-widest
                       hover:brightness-110
                       transition-all duration-200 ease-out"
          >
            {data.cta_button_text || 'Get Started'}
          </a>

          {/* -- Mobile Hamburger -- */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden relative w-10 h-10 flex items-center justify-center
                       text-gray-400 hover:text-primary
                       transition-colors duration-200"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
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
                  <line x1="4" y1="6" x2="20" y2="6" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="18" x2="20" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* -- Mobile Dropdown -- */}
      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
          menuOpen ? 'max-h-80 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-4 pt-1 space-y-1 border-t border-gray-800 bg-gray-950">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-widest
                         hover:text-primary hover:bg-white/5
                         transition-colors duration-200"
            >
              {link.label}
            </a>
          ))}
          <a
            href="#contact"
            onClick={() => setMenuOpen(false)}
            className="block w-full text-center mt-2 px-5 py-3 bg-primary text-white
                       text-xs font-black uppercase tracking-widest
                       hover:brightness-110
                       transition-all duration-200"
          >
            {data.cta_button_text || 'Get Started'}
          </a>
        </div>
      </div>
    </nav>
  )
}
