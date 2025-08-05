<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to CharForge
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          AI-Powered Character LoRA Creation
        </p>
      </div>
      
      <Card class="p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
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
              placeholder="Enter your username"
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
              placeholder="Enter your password"
            />
          </div>
          
          <Button
            type="submit"
            :disabled="authStore.isLoading"
            class="w-full"
          >
            <span v-if="authStore.isLoading">Signing in...</span>
            <span v-else>Sign in</span>
          </Button>
        </form>
        
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600">
            Don't have an account?
            <router-link to="/register" class="font-medium text-primary hover:text-primary/80">
              Sign up
            </router-link>
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Card from '@/components/ui/Card.vue'

const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  try {
    await authStore.login(form)
  } catch (error) {
    // Error is handled in the store
  }
}
</script>
