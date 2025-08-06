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
    return !!token.value && !!user.value
  })
  
  // Actions
  const checkAuthEnabled = async () => {
    try {
      // Try to access auth endpoint to see if it exists
      await fetch('/api/auth/me', { method: 'GET' })
      authEnabled.value = true
    } catch (error) {
      // If auth endpoint doesn't exist, auth is disabled
      authEnabled.value = false
      // Set a default user when auth is disabled
      user.value = {
        id: 1,
        username: 'default_user',
        email: 'default@charforge.local',
        is_active: true
      }
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

    // Actions
    initializeAuth,
    checkAuthEnabled,
    login,
    register,
    logout,
    verifyToken
  }
})
