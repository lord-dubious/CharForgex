<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Join CharForge to start creating character LoRAs
        </p>
      </div>
      
      <Card class="p-8">
        <form @submit.prevent="handleRegister" class="space-y-6">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">
              Username
            </label>
            <Input
              id="username"
              v-model="form.username"
              type="text"
              required
              class="mt-1"
              placeholder="Choose a username"
            />
          </div>
          
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email
            </label>
            <Input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="mt-1"
              placeholder="Enter your email"
            />
          </div>
          
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              required
              class="mt-1"
              placeholder="Choose a password"
            />
          </div>
          
          <Button
            type="submit"
            :disabled="authStore.isLoading"
            class="w-full"
          >
            <span v-if="authStore.isLoading">Creating account...</span>
            <span v-else>Create account</span>
          </Button>
        </form>
        
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600">
            Already have an account?
            <router-link to="/login" class="font-medium text-primary hover:text-primary/80">
              Sign in
            </router-link>
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Card from '@/components/ui/Card.vue'

const authStore = useAuthStore()
const toast = useToast()

const form = reactive({
  username: '',
  email: '',
  password: ''
})

const handleRegister = async () => {
  // Client-side validation
  if (!form.username || form.username.length < 3 || form.username.length > 50) {
    toast.error('Username must be between 3 and 50 characters')
    return
  }

  if (!form.email || !isValidEmail(form.email)) {
    toast.error('Please enter a valid email address')
    return
  }

  if (!form.password || form.password.length < 8) {
    toast.error('Password must be at least 8 characters')
    return
  }

  try {
    await authStore.register(form)
  } catch (error) {
    // Error is handled in the store
  }
}

const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}
</script>
