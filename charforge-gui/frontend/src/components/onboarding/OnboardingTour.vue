<template>
  <div v-if="onboardingStore.isActive" class="fixed inset-0 z-50">
    <!-- Overlay -->
    <div class="absolute inset-0 bg-black/50" @click="handleOverlayClick" />
    
    <!-- Spotlight for targeted elements -->
    <div
      v-if="currentTarget"
      class="absolute border-4 border-primary rounded-lg pointer-events-none transition-all duration-300"
      :style="spotlightStyle"
    />
    
    <!-- Tour popup -->
    <div
      class="absolute bg-background border border-border rounded-lg shadow-xl max-w-sm w-full p-6 transition-all duration-300"
      :style="popupStyle"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-bold">
            {{ onboardingStore.currentStepIndex + 1 }}
          </div>
          <h3 class="text-lg font-semibold">{{ onboardingStore.currentStep?.title }}</h3>
        </div>
        <Button @click="onboardingStore.skipOnboarding" variant="ghost" size="sm">
          <X class="h-4 w-4" />
        </Button>
      </div>
      
      <!-- Content -->
      <div class="mb-6">
        <p class="text-muted-foreground">{{ onboardingStore.currentStep?.description }}</p>
      </div>
      
      <!-- Progress -->
      <div class="mb-4">
        <div class="flex justify-between text-xs text-muted-foreground mb-2">
          <span>Step {{ onboardingStore.currentStepIndex + 1 }} of {{ onboardingStore.steps.length }}</span>
          <span>{{ Math.round(((onboardingStore.currentStepIndex + 1) / onboardingStore.steps.length) * 100) }}%</span>
        </div>
        <div class="w-full bg-muted rounded-full h-2">
          <div
            class="bg-primary h-2 rounded-full transition-all duration-300"
            :style="{ width: `${((onboardingStore.currentStepIndex + 1) / onboardingStore.steps.length) * 100}%` }"
          />
        </div>
      </div>
      
      <!-- Actions -->
      <div class="flex justify-between">
        <div>
          <Button
            v-if="!onboardingStore.isFirstStep"
            @click="onboardingStore.previousStep"
            variant="outline"
            size="sm"
          >
            <ChevronLeft class="mr-2 h-4 w-4" />
            Back
          </Button>
        </div>
        
        <div class="flex space-x-2">
          <Button
            v-if="onboardingStore.currentStep?.canSkip"
            @click="onboardingStore.skipOnboarding"
            variant="ghost"
            size="sm"
          >
            Skip Tour
          </Button>
          <Button
            @click="handleNext"
            size="sm"
          >
            {{ onboardingStore.isLastStep ? 'Finish' : 'Next' }}
            <ChevronRight v-if="!onboardingStore.isLastStep" class="ml-2 h-4 w-4" />
            <Check v-else class="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ChevronLeft, ChevronRight, X, Check } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useOnboardingStore } from '@/stores/onboarding'

const onboardingStore = useOnboardingStore()

const currentTarget = ref<HTMLElement | null>(null)
const popupPosition = ref({ x: 0, y: 0 })

const spotlightStyle = computed(() => {
  if (!currentTarget.value) return {}
  
  const rect = currentTarget.value.getBoundingClientRect()
  return {
    left: `${rect.left - 8}px`,
    top: `${rect.top - 8}px`,
    width: `${rect.width + 16}px`,
    height: `${rect.height + 16}px`,
  }
})

const popupStyle = computed(() => {
  return {
    left: `${popupPosition.value.x}px`,
    top: `${popupPosition.value.y}px`,
  }
})

const updateTargetElement = () => {
  const step = onboardingStore.currentStep
  if (!step?.target) {
    currentTarget.value = null
    centerPopup()
    return
  }
  
  const element = document.querySelector(step.target) as HTMLElement
  if (element) {
    currentTarget.value = element
    positionPopup(element, step.position || 'bottom')
    
    // Scroll element into view
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } else {
    currentTarget.value = null
    centerPopup()
  }
}

const positionPopup = (target: HTMLElement, position: string) => {
  const rect = target.getBoundingClientRect()
  const popupWidth = 384 // max-w-sm = 384px
  const popupHeight = 300 // estimated height
  const margin = 16
  
  let x = 0
  let y = 0
  
  switch (position) {
    case 'top':
      x = rect.left + (rect.width / 2) - (popupWidth / 2)
      y = rect.top - popupHeight - margin
      break
    case 'bottom':
      x = rect.left + (rect.width / 2) - (popupWidth / 2)
      y = rect.bottom + margin
      break
    case 'left':
      x = rect.left - popupWidth - margin
      y = rect.top + (rect.height / 2) - (popupHeight / 2)
      break
    case 'right':
      x = rect.right + margin
      y = rect.top + (rect.height / 2) - (popupHeight / 2)
      break
    default:
      x = rect.left + (rect.width / 2) - (popupWidth / 2)
      y = rect.bottom + margin
  }
  
  // Keep popup within viewport
  x = Math.max(margin, Math.min(x, window.innerWidth - popupWidth - margin))
  y = Math.max(margin, Math.min(y, window.innerHeight - popupHeight - margin))
  
  popupPosition.value = { x, y }
}

const centerPopup = () => {
  const popupWidth = 384
  const popupHeight = 300
  
  popupPosition.value = {
    x: (window.innerWidth / 2) - (popupWidth / 2),
    y: (window.innerHeight / 2) - (popupHeight / 2)
  }
}

const handleNext = () => {
  const step = onboardingStore.currentStep
  if (step?.action) {
    step.action()
  }
  onboardingStore.nextStep()
}

const handleOverlayClick = () => {
  // Only allow closing if current step can be skipped
  if (onboardingStore.currentStep?.canSkip) {
    onboardingStore.skipOnboarding()
  }
}

const handleResize = () => {
  updateTargetElement()
}

// Watch for step changes
watch(() => onboardingStore.currentStepIndex, () => {
  setTimeout(updateTargetElement, 100) // Small delay to ensure DOM updates
})

onMounted(() => {
  updateTargetElement()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>
