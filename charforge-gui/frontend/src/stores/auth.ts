import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { authApi } from '@/services/api'

export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  const toast = useToast()
  
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const isLoading = ref(false)
  const authEnabled = ref<boolean>(true) // Will be set based on backend config

  // Getters
  const isAuthenticated = computed(() => {
    // If auth is disabled, always return true
    if (!authEnabled.value) return true
    // isAuthenticated is true if a token exists, regardless of user data loading state
    return !!token.value
  })

  // isAuthLoading is true if token exists but user data is not yet loaded
  const isAuthLoading = computed(() => !!token.value && !user.value)
  
  // Actions
  const checkAuthEnabled = async () => {
    try {
      // Use dedicated config endpoint to check auth status
      const response = await fetch('/api/auth/config', { method: 'GET' })

      if (response.ok) {
        const config = await response.json()
        authEnabled.value = config.auth_enabled

        // Set a default user when auth is disabled
        if (!config.auth_enabled) {
          user.value = {
            id: 1,
            username: 'default_user',
            email: 'default@charforge.local',
            is_active: true
          }
        }
      } else if (response.status === 404) {
        // Config endpoint doesn't exist, assume auth is disabled
        authEnabled.value = false
        user.value = {
          id: 1,
          username: 'default_user',
          email: 'default@charforge.local',
          is_active: true
        }
      } else {
        // Server error, assume auth is enabled for safety
        authEnabled.value = true
      }
    } catch (error) {
      // Network error, assume auth is enabled for safety
      console.warn('Failed to check auth config, assuming auth is enabled:', error)
      authEnabled.value = true
    }
  }

  const initializeAuth = async () => {
    await checkAuthEnabled()

    if (!authEnabled.value) {
      // Auth is disabled, no need to check tokens
      return
    }

    const savedToken = localStorage.getItem('auth_token')
    if (savedToken) {
      token.value = savedToken
      try {
        const userData = await authApi.getMe()
        user.value = userData
      } catch (error) {
        // Token is invalid, clear it
        logout()
      }
    }
  }
  
  const login = async (credentials: LoginCredentials) => {
    isLoading.value = true
    try {
      const response = await authApi.login(credentials)
      token.value = response.access_token
      localStorage.setItem('auth_token', response.access_token)
      
      // Get user data
      const userData = await authApi.getMe()
      user.value = userData
      
      toast.success('Login successful!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  const register = async (data: RegisterData) => {
    isLoading.value = true
    try {
      await authApi.register(data)
      toast.success('Registration successful! Please login.')
      router.push('/login')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('auth_token')
    router.push('/login')
    toast.info('Logged out successfully')
  }
  
  const verifyToken = async () => {
    try {
      await authApi.verifyToken()
      return true
    } catch (error) {
      logout()
      return false
    }
  }
  
  return {
    // State
    user,
    token,
    isLoading,
    authEnabled,

    // Getters
    isAuthenticated,
    isAuthLoading,

    // Actions
    initializeAuth,
    checkAuthEnabled,
    login,
    register,
    logout,
    verifyToken
  }
})
