export default function Footer({ data }: { data: any }) {
  const navLinks = [
    { label: 'About', href: '#about' },
    { label: 'Services', href: '#services' },
    { label: 'Testimonials', href: '#testimonials' },
    { label: 'Contact', href: '#contact' },
  ]

  return (
    <footer className="bg-gray-900 text-gray-400 py-16 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Top row - Business identity */}
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold font-heading text-white mb-2">
            {data.business_name}
          </h2>
          {data.address && (
            <p className="text-sm">{data.address}</p>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-800 my-8" />

        {/* Navigation links */}
        <nav className="flex flex-wrap justify-center gap-8 mb-10">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-gray-400 hover:text-white transition-colors duration-200 text-sm font-medium"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Divider */}
        <div className="border-t border-gray-800 my-8" />

        {/* Copyright */}
        <p className="text-center text-sm text-gray-500">
          &copy; {new Date().getFullYear()} {data.business_name}. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
