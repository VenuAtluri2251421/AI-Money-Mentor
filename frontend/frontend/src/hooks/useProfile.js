import { useState, useEffect, useCallback } from 'react'
import { getProfile, saveProfile } from '../api/client'

/**
 * useProfile — load and persist the user's financial profile.
 * Falls back to localStorage when the backend is unavailable.
 */
export function useProfile(userId) {
  const [profile, setProfile]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error,   setError]     = useState(null)

  // Load on mount
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        if (userId) {
          const res = await getProfile(userId)
          setProfile(res.data)
          localStorage.setItem('artha_profile', JSON.stringify(res.data))
        } else {
          const cached = localStorage.getItem('artha_profile')
          if (cached) setProfile(JSON.parse(cached))
        }
      } catch (err) {
        const cached = localStorage.getItem('artha_profile')
        if (cached) setProfile(JSON.parse(cached))
        else setError(err?.message || 'Failed to load profile')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [userId])

  // Update profile both locally and on server
  const updateProfile = useCallback(async (newData) => {
    const merged = { ...profile, ...newData }
    setProfile(merged)
    localStorage.setItem('artha_profile', JSON.stringify(merged))
    try {
      await saveProfile(merged)
    } catch {
      // fail silently — optimistic update already applied
    }
  }, [profile])

  return { profile, loading, error, updateProfile }
}
