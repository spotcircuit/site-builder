import { describe, it, expect } from 'vitest'
import { getDownloadUrl, getApiBase } from '../../services/api'

describe('API Service', () => {
  describe('getDownloadUrl', () => {
    it('returns correct download URL', () => {
      const url = getDownloadUrl('test-job-123')
      expect(url).toBe('http://localhost:9405/api/job/test-job-123/download')
    })

    it('handles special characters in job ID', () => {
      const url = getDownloadUrl('abc-def-123-456')
      expect(url).toContain('abc-def-123-456')
    })
  })

  describe('getApiBase', () => {
    it('returns the API base URL', () => {
      const base = getApiBase()
      expect(base).toBe('http://localhost:9405')
    })
  })
})
