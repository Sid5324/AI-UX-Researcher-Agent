'use client'

import { create } from 'zustand'
import { authApi, checkBackendHealth } from '@/lib/api'
import axios from 'axios'

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
  backendOnline: boolean
  init: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  checkBackend: () => Promise<boolean>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,
  error: null,
  backendOnline: true,

  init: async () => {
    if (typeof window === 'undefined') return

    // First check if backend is reachable
    const backendAvailable = await checkBackendHealth()
    set({ backendOnline: backendAvailable })

    if (!backendAvailable) {
      set({ initialized: true, user: null, error: 'Backend server is offline' })
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ initialized: true, user: null })
      return
    }

    set({ loading: true, error: null })
    try {
      const user = await authApi.me()
      set({ user, initialized: true, loading: false, error: null })
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      const errorMsg = axios.isAxiosError(error) && error.code === 'ECONNREFUSED'
        ? 'Backend server is offline'
        : 'Session expired'
      set({ user: null, initialized: true, loading: false, error: errorMsg })
    }
  },

  checkBackend: async () => {
    const isOnline = await checkBackendHealth()
    set({ backendOnline: isOnline })
    return isOnline
  },

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const data = await authApi.login(email, password)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user, loading: false, backendOnline: true, error: null })
    } catch (error) {
      const errorMsg = axios.isAxiosError(error) && error.code === 'ECONNREFUSED'
        ? 'Cannot connect to backend server'
        : 'Login failed - check your credentials'
      set({ loading: false, error: errorMsg, backendOnline: !axios.isAxiosError(error) || error.code !== 'ECONNREFUSED' })
      throw error
    }
  },

  register: async (email, password, name) => {
    set({ loading: true, error: null })
    try {
      const data = await authApi.register(email, password, name)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user, loading: false, backendOnline: true, error: null })
    } catch (error) {
      const errorMsg = axios.isAxiosError(error) && error.code === 'ECONNREFUSED'
        ? 'Cannot connect to backend server'
        : 'Registration failed'
      set({ loading: false, error: errorMsg, backendOnline: !axios.isAxiosError(error) || error.code !== 'ECONNREFUSED' })
      throw error
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
