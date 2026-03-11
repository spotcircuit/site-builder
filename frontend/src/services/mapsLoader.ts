let mapsPromise: Promise<void> | null = null

export function ensureGoogleMapsLoaded(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()

  const w = window as any
  if (w.google?.maps?.places) return Promise.resolve()

  if (w.google?.maps && typeof w.google.maps.importLibrary === 'function') {
    return w.google.maps.importLibrary('places').then(() => {})
  }

  if (mapsPromise) return mapsPromise

  mapsPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector(
      'script[src*="maps.googleapis.com/maps/api/js"]'
    ) as HTMLScriptElement | null

    if (existing) {
      const onReady = () => {
        if (w.google?.maps?.importLibrary) {
          w.google.maps.importLibrary('places').then(() => resolve()).catch(reject)
          return
        }
        resolve()
      }
      existing.addEventListener('load', onReady, { once: true })
      existing.addEventListener('error', () => reject(new Error('Google Maps failed to load')), { once: true })
      if (w.google?.maps?.places) resolve()
      return
    }

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
    if (!apiKey) {
      console.warn('[SiteBuilder] VITE_GOOGLE_MAPS_API_KEY not set — autocomplete disabled')
      resolve()
      return
    }

    const script = document.createElement('script')
    script.async = true
    script.defer = true
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`
    script.onload = () => {
      if (w.google?.maps?.importLibrary) {
        w.google.maps.importLibrary('places').then(() => resolve()).catch(reject)
        return
      }
      resolve()
    }
    script.onerror = () => reject(new Error('Google Maps failed to load'))
    document.head.appendChild(script)
  })

  return mapsPromise
}
