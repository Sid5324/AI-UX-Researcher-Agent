'use client'

import { create } from 'zustand'
import { authApi } from '@/lib/api'

type User = {
  id: string
  email: string
  name: string
  role: string
}

type AuthState = {
  user: User | null
  loading: boolean
  initialized: boolean
  error: string | null
  init: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,
  error: null,

  init: async () => {
    if (typeof window === 'undefined') return
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ initialized: true, user: null })
      return
    }

    set({ loading: true, error: null })
    try {
      const user = await authApi.me()
      set({ user, initialized: true, loading: false })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, initialized: true, loading: false })
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const data = await authApi.login(email, password)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user, loading: false })
    } catch (e) {
      set({ loading: false, error: 'Login failed' })
      throw e
    }
  },

  register: async (email, password, name) => {
    set({ loading: true, error: null })
    try {
      const data = await authApi.register(email, password, name)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user, loading: false })
    } catch (e) {
      set({ loading: false, error: 'Registration failed' })
      throw e
    }
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
    set({ user: null, initialized: true, loading: false, error: null })
  },
}))
