<template>
  <div id="app" class="min-h-screen bg-background">
    <router-view />

    <!-- Onboarding Components -->
    <WelcomeModal />
    <OnboardingTour />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import WelcomeModal from '@/components/onboarding/WelcomeModal.vue'
import OnboardingTour from '@/components/onboarding/OnboardingTour.vue'

const authStore = useAuthStore()
const onboardingStore = useOnboardingStore()

onMounted(() => {
  // Try to restore authentication state from localStorage
  authStore.initializeAuth()

  // Initialize onboarding state
  onboardingStore.initializeOnboarding()
})
</script>

<style scoped>
#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
