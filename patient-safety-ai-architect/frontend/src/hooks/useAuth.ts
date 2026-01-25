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
          // Use URLSearchParams for form-urlencoded data
          const formData = new URLSearchParams()
          formData.append('username', username)
          formData.append('password', password)

          const response = await api.post('/api/auth/login', formData, {
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

          // Transform snake_case to camelCase
          const userData = userResponse.data
          set({
            user: {
              id: userData.id,
              username: userData.username,
              email: userData.email,
              fullName: userData.full_name,
              role: userData.role,
              department: userData.department,
            },
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
          // Transform snake_case to camelCase
          const userData = response.data
          set({
            user: {
              id: userData.id,
              username: userData.username,
              email: userData.email,
              fullName: userData.full_name,
              role: userData.role,
              department: userData.department,
            },
            isAuthenticated: true,
            isLoading: false,
          })
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
