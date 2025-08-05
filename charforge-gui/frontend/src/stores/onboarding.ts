import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface OnboardingStep {
  id: string
  title: string
  description: string
  target?: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  action?: () => void
  canSkip?: boolean
  isCompleted?: boolean
}

export const useOnboardingStore = defineStore('onboarding', () => {
  const isActive = ref(false)
  const currentStepIndex = ref(0)
  const completedSteps = ref<string[]>([])
  const hasCompletedOnboarding = ref(false)

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to CharForge!',
      description: 'Let\'s take a quick tour to get you started with AI character LoRA creation.',
      canSkip: true
    },
    {
      id: 'settings',
      title: 'Configure API Keys',
      description: 'First, let\'s set up your API keys. These are required for training and generating images.',
      target: '[data-tour="settings-link"]',
      position: 'bottom'
    },
    {
      id: 'media-upload',
      title: 'Upload Reference Images',
      description: 'Upload images of your character. You can upload multiple images to create a dataset.',
      target: '[data-tour="media-link"]',
      position: 'bottom'
    },
    {
      id: 'create-character',
      title: 'Create Your Character',
      description: 'Create a new character profile and configure training settings.',
      target: '[data-tour="create-character"]',
      position: 'bottom'
    },
    {
      id: 'training',
      title: 'Monitor Training',
      description: 'Watch your character training progress in real-time.',
      target: '[data-tour="training-link"]',
      position: 'bottom'
    },
    {
      id: 'inference',
      title: 'Generate Images',
      description: 'Once training is complete, generate images with your character LoRA.',
      target: '[data-tour="inference-link"]',
      position: 'bottom'
    },
    {
      id: 'gallery',
      title: 'View Results',
      description: 'Browse and manage your generated images in the gallery.',
      target: '[data-tour="gallery-link"]',
      position: 'bottom'
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      description: 'You\'re ready to start creating amazing AI characters. Happy creating!',
      canSkip: false
    }
  ]

  const currentStep = computed(() => steps[currentStepIndex.value])
  const isLastStep = computed(() => currentStepIndex.value === steps.length - 1)
  const isFirstStep = computed(() => currentStepIndex.value === 0)

  const startOnboarding = () => {
    isActive.value = true
    currentStepIndex.value = 0
  }

  const nextStep = () => {
    if (currentStep.value) {
      markStepCompleted(currentStep.value.id)
    }
    
    if (isLastStep.value) {
      completeOnboarding()
    } else {
      currentStepIndex.value++
    }
  }

  const previousStep = () => {
    if (!isFirstStep.value) {
      currentStepIndex.value--
    }
  }

  const skipOnboarding = () => {
    completeOnboarding()
  }

  const completeOnboarding = () => {
    isActive.value = false
    hasCompletedOnboarding.value = true
    localStorage.setItem('charforge_onboarding_completed', 'true')
  }

  const markStepCompleted = (stepId: string) => {
    if (!completedSteps.value.includes(stepId)) {
      completedSteps.value.push(stepId)
    }
  }

  const resetOnboarding = () => {
    isActive.value = false
    currentStepIndex.value = 0
    completedSteps.value = []
    hasCompletedOnboarding.value = false
    localStorage.removeItem('charforge_onboarding_completed')
  }

  const initializeOnboarding = () => {
    const completed = localStorage.getItem('charforge_onboarding_completed')
    hasCompletedOnboarding.value = completed === 'true'
  }

  const goToStep = (stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      currentStepIndex.value = stepIndex
    }
  }

  return {
    // State
    isActive,
    currentStepIndex,
    completedSteps,
    hasCompletedOnboarding,
    steps,
    
    // Getters
    currentStep,
    isLastStep,
    isFirstStep,
    
    // Actions
    startOnboarding,
    nextStep,
    previousStep,
    skipOnboarding,
    completeOnboarding,
    markStepCompleted,
    resetOnboarding,
    initializeOnboarding,
    goToStep
  }
})
