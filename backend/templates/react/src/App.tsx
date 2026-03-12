import { useState, useEffect } from 'react'
import _data from './data.json'

import Navbar from './components/Navbar'
import Hero from './components/Hero'
import SocialProof from './components/SocialProof'
import About from './components/About'
import Services from './components/Services'
import WhyChooseUs from './components/WhyChooseUs'
import HowItWorks from './components/HowItWorks'
import Gallery from './components/Gallery'
import Testimonials from './components/Testimonials'
import FAQ from './components/FAQ'
import CTA from './components/CTA'
import Contact from './components/Contact'
import Footer from './components/Footer'
import LocalBusinessSchema from './components/LocalBusinessSchema'

// Section type -> component registry for dynamic rendering
const SECTION_REGISTRY: Record<string, React.ComponentType<{ data: any }>> = {
  'hero': Hero,
  'social-proof': SocialProof,
  'about': About,
  'services': Services,
  'why-choose-us': WhyChooseUs,
  'how-it-works': HowItWorks,
  'gallery': Gallery,
  'testimonials': Testimonials,
  'faq': FAQ,
  'cta': CTA,
  'contact': Contact,
  'footer': Footer,
}

// Default section order when data.sections is not present (backwards compat)
const DEFAULT_SECTIONS = [
  { id: 'hero', type: 'hero', enabled: true, order: 0 },
  { id: 'social-proof', type: 'social-proof', enabled: true, order: 1 },
  { id: 'about', type: 'about', enabled: true, order: 2 },
  { id: 'services', type: 'services', enabled: true, order: 3 },
  { id: 'why-choose-us', type: 'why-choose-us', enabled: true, order: 4 },
  { id: 'how-it-works', type: 'how-it-works', enabled: true, order: 5 },
  { id: 'gallery', type: 'gallery', enabled: true, order: 6 },
  { id: 'testimonials', type: 'testimonials', enabled: true, order: 7 },
  { id: 'faq', type: 'faq', enabled: true, order: 8 },
  { id: 'cta', type: 'cta', enabled: true, order: 9 },
  { id: 'contact', type: 'contact', enabled: true, order: 10 },
  { id: 'footer', type: 'footer', enabled: true, order: 11 },
]

function App() {
  // Quick Preview: accept live data updates via postMessage from parent editor
  const [data, setData] = useState(_data as any)

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data?.type === 'QUICK_PREVIEW' && event.data.payload) {
        setData(event.data.payload)
      }
      if (event.data?.type === 'SCROLL_TO_SECTION' && event.data.sectionId) {
        const el = document.getElementById(event.data.sectionId)
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  // Dynamic section rendering from sections array
  const sections = (data.sections || DEFAULT_SECTIONS)
    .filter((s: any) => s.enabled)
    .sort((a: any, b: any) => a.order - b.order)

  return (
    <div className={`min-h-screen bg-gray-50 text-gray-800 antialiased font-body font-scale-${data.font_scale || 'default'}`}>
      <LocalBusinessSchema data={data} />
      <Navbar data={data} />
      {sections.map((section: any) => {
        const Component = SECTION_REGISTRY[section.type]
        if (!Component) return null
        return <Component key={section.id} data={data} />
      })}
    </div>
  )
}

export default App
