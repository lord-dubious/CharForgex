<template>
  <div
    v-if="showWelcome"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
  >
    <div class="bg-background rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto">
      <div class="p-8">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="mx-auto w-20 h-20 bg-gradient-to-br from-primary to-primary/60 rounded-full flex items-center justify-center mb-4">
            <Sparkles class="h-10 w-10 text-primary-foreground" />
          </div>
          <h1 class="text-3xl font-bold mb-2">Welcome to CharForge!</h1>
          <p class="text-lg text-muted-foreground">
            AI-Powered Character LoRA Creation Made Simple
          </p>
        </div>

        <!-- Features -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Upload class="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <h3 class="font-semibold mb-1">Easy Upload</h3>
              <p class="text-sm text-muted-foreground">
                Upload multiple images to create comprehensive character datasets
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Zap class="h-4 w-4 text-green-600" />
            </div>
            <div>
              <h3 class="font-semibold mb-1">AI Training</h3>
              <p class="text-sm text-muted-foreground">
                Automated LoRA training with real-time progress monitoring
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Wand2 class="h-4 w-4 text-purple-600" />
            </div>
            <div>
              <h3 class="font-semibold mb-1">Image Generation</h3>
              <p class="text-sm text-muted-foreground">
                Generate stunning images with your trained character LoRAs
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Settings class="h-4 w-4 text-orange-600" />
            </div>
            <div>
              <h3 class="font-semibold mb-1">Full Control</h3>
              <p class="text-sm text-muted-foreground">
                Customize trigger words, captions, and training parameters
              </p>
            </div>
          </div>
        </div>

        <!-- Quick Start Steps -->
        <div class="bg-muted rounded-lg p-6 mb-8">
          <h3 class="font-semibold mb-4 flex items-center">
            <BookOpen class="mr-2 h-5 w-5" />
            Quick Start Guide
          </h3>
          <div class="space-y-3">
            <div class="flex items-center space-x-3">
              <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-bold">1</div>
              <span class="text-sm">Configure your API keys in Settings</span>
            </div>
            <div class="flex items-center space-x-3">
              <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-bold">2</div>
              <span class="text-sm">Upload reference images of your character</span>
            </div>
            <div class="flex items-center space-x-3">
              <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-bold">3</div>
              <span class="text-sm">Create and train your character LoRA</span>
            </div>
            <div class="flex items-center space-x-3">
              <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-xs font-bold">4</div>
              <span class="text-sm">Generate amazing images with your character</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-col sm:flex-row gap-3">
          <Button @click="startTour" class="flex-1">
            <Play class="mr-2 h-4 w-4" />
            Take the Tour
          </Button>
          <Button @click="skipToSettings" variant="outline" class="flex-1">
            <Settings class="mr-2 h-4 w-4" />
            Skip to Settings
          </Button>
          <Button @click="dismissWelcome" variant="ghost">
            Skip
          </Button>
        </div>

        <!-- Don't show again -->
        <div class="mt-6 pt-6 border-t border-border">
          <label class="flex items-center space-x-2 text-sm text-muted-foreground cursor-pointer">
            <input
              v-model="dontShowAgain"
              type="checkbox"
              class="rounded border-input"
            />
            <span>Don't show this welcome message again</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Sparkles, Upload, Zap, Wand2, Settings, BookOpen, Play
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useOnboardingStore } from '@/stores/onboarding'

const router = useRouter()
const onboardingStore = useOnboardingStore()

const showWelcome = ref(false)
const dontShowAgain = ref(false)

const startTour = () => {
  if (dontShowAgain.value) {
    localStorage.setItem('charforge_welcome_dismissed', 'true')
  }
  showWelcome.value = false
  onboardingStore.startOnboarding()
}

const skipToSettings = () => {
  if (dontShowAgain.value) {
    localStorage.setItem('charforge_welcome_dismissed', 'true')
  }
  showWelcome.value = false
  router.push('/settings')
}

const dismissWelcome = () => {
  if (dontShowAgain.value) {
    localStorage.setItem('charforge_welcome_dismissed', 'true')
  }
  showWelcome.value = false
  onboardingStore.completeOnboarding()
}

onMounted(() => {
  // Show welcome if user hasn't completed onboarding and hasn't dismissed welcome
  const hasCompletedOnboarding = localStorage.getItem('charforge_onboarding_completed') === 'true'
  const hasWelcomeDismissed = localStorage.getItem('charforge_welcome_dismissed') === 'true'
  
  if (!hasCompletedOnboarding && !hasWelcomeDismissed) {
    showWelcome.value = true
  }
})
</script>
