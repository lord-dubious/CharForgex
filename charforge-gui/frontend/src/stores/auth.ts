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
  
  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  // Actions
  const initializeAuth = async () => {
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
    
    // Getters
    isAuthenticated,
    
    // Actions
    initializeAuth,
    login,
    register,
    logout,
    verifyToken
  }
})
