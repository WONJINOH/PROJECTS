import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/utils/api'

interface User {
  id: number
  username: string
  email: string
  fullName: string
  role: string
  department?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,

      login: async (username: string, password: string) => {
        try {
          const response = await api.post('/api/auth/login', {
            username,
            password,
          }, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          })

          const { access_token } = response.data
          set({ token: access_token })

          // Get user info
          const userResponse = await api.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${access_token}` },
          })

          set({
            user: userResponse.data,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ user: null, token: null, isAuthenticated: false, isLoading: false })
          throw error
        }
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },

      checkAuth: async () => {
        const { token } = get()
        if (!token) {
          set({ isLoading: false })
          return
        }

        try {
          const response = await api.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${token}` },
          })
          set({ user: response.data, isAuthenticated: true, isLoading: false })
        } catch {
          set({ user: null, token: null, isAuthenticated: false, isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
