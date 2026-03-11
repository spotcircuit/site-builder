import _data from './data.json'

// Cast to any so TS doesn't complain about fields added at build time
const data = _data as any
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

function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 antialiased font-body">
      <LocalBusinessSchema data={data} />
      <Navbar data={data} />
      <Hero data={data} />
      {data.rating && <SocialProof data={data} />}
      <About data={data} />
      <Services data={data} />
      {data.why_choose_us?.length > 0 && <WhyChooseUs data={data} />}
      {data.process_steps?.length > 0 && <HowItWorks data={data} />}
      {(data.photos?.length > 0 || data.website_images?.length > 0 || data.ai_gallery_images?.length > 0) && <Gallery data={data} />}
      {data.testimonials?.length > 0 && <Testimonials data={data} />}
      {data.faq_items?.length > 0 && <FAQ data={data} />}
      <CTA data={data} />
      <Contact data={data} />
      <Footer data={data} />
    </div>
  )
}

export default App
