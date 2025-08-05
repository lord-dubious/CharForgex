<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Generate Images</h1>
        <p class="text-muted-foreground">
          Create images using your trained character LoRAs
        </p>
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <!-- Generation Form -->
        <div class="lg:col-span-2 space-y-6">
          <form @submit.prevent="generateImages" class="space-y-6">
            <!-- Character Selection -->
            <Card class="p-6">
              <h3 class="text-lg font-semibold mb-4">Character Selection</h3>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium mb-2">Select Character</label>
                  <select
                    v-model="form.character_id"
                    class="w-full h-10 px-3 py-2 border border-input rounded-md bg-background"
                    required
                  >
                    <option value="">Choose a character...</option>
                    <option
                      v-for="character in availableCharacters"
                      :key="character.id"
                      :value="character.id"
                    >
                      {{ character.name }}
                    </option>
                  </select>
                  <p class="text-xs text-muted-foreground mt-1">
                    Only characters with completed training are shown
                  </p>
                </div>

                <div v-if="selectedCharacter" class="flex items-center space-x-3 p-3 bg-muted rounded-lg">
                  <div class="w-12 h-12 bg-background rounded overflow-hidden">
                    <img
                      v-if="selectedCharacter.preview_image"
                      :src="selectedCharacter.preview_image"
                      :alt="selectedCharacter.name"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <User class="h-6 w-6 text-muted-foreground" />
                    </div>
                  </div>
                  <div>
                    <p class="font-medium">{{ selectedCharacter.name }}</p>
                    <p class="text-sm text-muted-foreground">
                      Completed {{ formatDate(selectedCharacter.completed_at) }}
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            <!-- Prompt Configuration -->
            <Card class="p-6">
              <h3 class="text-lg font-semibold mb-4">Prompt Configuration</h3>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium mb-2">Prompt</label>
                  <textarea
                    v-model="form.prompt"
                    rows="4"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background resize-none"
                    placeholder="Describe the image you want to generate..."
                    required
                  ></textarea>
                  <p class="text-xs text-muted-foreground mt-1">
                    Be descriptive! Include details about pose, clothing, background, lighting, etc.
                  </p>
                </div>

                <div class="flex items-center space-x-2">
                  <input
                    id="optimize_prompt"
                    v-model="form.do_optimize_prompt"
                    type="checkbox"
                    class="rounded border-input"
                  />
                  <label for="optimize_prompt" class="text-sm font-medium">
                    Optimize prompt automatically
                  </label>
                </div>

                <div class="flex items-center space-x-2">
                  <input
                    id="fix_outfit"
                    v-model="form.fix_outfit"
                    type="checkbox"
                    class="rounded border-input"
                  />
                  <label for="fix_outfit" class="text-sm font-medium">
                    Fix outfit to reference image
                  </label>
                </div>
              </div>
            </Card>

            <!-- Generation Settings -->
            <Card class="p-6">
              <h3 class="text-lg font-semibold mb-4">Generation Settings</h3>

              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <label class="block text-sm font-medium mb-2">
                    LoRA Weight: {{ form.lora_weight }}
                  </label>
                  <input
                    v-model.number="form.lora_weight"
                    type="range"
                    min="0.1"
                    max="1.5"
                    step="0.05"
                    class="w-full"
                  />
                  <p class="text-xs text-muted-foreground mt-1">
                    Higher = more character influence (recommended: 0.65-0.85)
                  </p>
                </div>

                <div>
                  <label class="block text-sm font-medium mb-2">Image Size</label>
                  <select
                    v-model="form.test_dim"
                    class="w-full h-10 px-3 py-2 border border-input rounded-md bg-background"
                  >
                    <option value="512">512x512</option>
                    <option value="768">768x768</option>
                    <option value="1024">1024x1024</option>
                    <option value="1536">1536x1536</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium mb-2">Number of Images</label>
                  <Input
                    v-model.number="form.batch_size"
                    type="number"
                    min="1"
                    max="8"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium mb-2">Inference Steps</label>
                  <Input
                    v-model.number="form.num_inference_steps"
                    type="number"
                    min="10"
                    max="100"
                    step="5"
                  />
                  <p class="text-xs text-muted-foreground mt-1">
                    More steps = higher quality but slower generation
                  </p>
                </div>
              </div>

              <div class="mt-4 space-y-2">
                <div class="flex items-center space-x-2">
                  <input
                    id="safety_check"
                    v-model="form.safety_check"
                    type="checkbox"
                    class="rounded border-input"
                  />
                  <label for="safety_check" class="text-sm font-medium">
                    Enable safety check
                  </label>
                </div>

                <div class="flex items-center space-x-2">
                  <input
                    id="face_enhance"
                    v-model="form.face_enhance"
                    type="checkbox"
                    class="rounded border-input"
                  />
                  <label for="face_enhance" class="text-sm font-medium">
                    Enable face enhancement
                  </label>
                </div>
              </div>
            </Card>

            <!-- Generate Button -->
            <Button
              type="submit"
              :disabled="!canGenerate || isGenerating"
              class="w-full"
              size="lg"
            >
              <Wand2 class="mr-2 h-5 w-5" />
              {{ isGenerating ? 'Generating...' : 'Generate Images' }}
            </Button>
          </form>
        </div>

        <!-- Recent Generations -->
        <div class="space-y-6">
          <Card class="p-6">
            <h3 class="text-lg font-semibold mb-4">Recent Generations</h3>

            <div v-if="recentJobs.length === 0" class="text-center py-8">
              <div class="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-3">
                <Image class="h-6 w-6 text-muted-foreground" />
              </div>
              <p class="text-sm text-muted-foreground">No generations yet</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="job in recentJobs.slice(0, 5)"
                :key="job.id"
                class="flex items-center space-x-3 p-3 bg-muted rounded-lg cursor-pointer hover:bg-accent transition-colors"
                @click="viewJob(job)"
              >
                <div class="w-10 h-10 bg-background rounded overflow-hidden">
                  <img
                    v-if="job.output_paths && job.output_paths[0]"
                    :src="job.output_paths[0]"
                    :alt="job.prompt"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <Image class="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium truncate">{{ job.character_name }}</p>
                  <p class="text-xs text-muted-foreground truncate">{{ job.prompt }}</p>
                </div>
                <StatusBadge :status="job.status" />
              </div>
            </div>

            <Button
              v-if="recentJobs.length > 5"
              @click="$router.push('/gallery')"
              variant="outline"
              class="w-full mt-4"
            >
              View All
            </Button>
          </Card>

          <!-- Quick Settings -->
          <Card class="p-6">
            <h3 class="text-lg font-semibold mb-4">Quick Presets</h3>

            <div class="space-y-2">
              <Button
                @click="applyPreset('portrait')"
                variant="outline"
                class="w-full justify-start"
              >
                Portrait Style
              </Button>
              <Button
                @click="applyPreset('landscape')"
                variant="outline"
                class="w-full justify-start"
              >
                Landscape Scene
              </Button>
              <Button
                @click="applyPreset('action')"
                variant="outline"
                class="w-full justify-start"
              >
                Action Pose
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <!-- Generation Results Modal -->
    <div
      v-if="showResults && currentJob"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="showResults = false"
    >
      <div
        class="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto"
        @click.stop
      >
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h3 class="text-lg font-semibold">Generation Results</h3>
              <p class="text-sm text-muted-foreground">{{ currentJob.character_name }}</p>
            </div>
            <Button @click="showResults = false" variant="ghost" size="sm">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div v-if="currentJob.status === 'running'" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p class="text-muted-foreground">Generating images...</p>
          </div>

          <div v-else-if="currentJob.output_paths" class="grid grid-cols-2 gap-4">
            <div
              v-for="(imagePath, index) in currentJob.output_paths"
              :key="index"
              class="aspect-square bg-muted rounded-lg overflow-hidden"
            >
              <img
                :src="imagePath"
                :alt="`Generated image ${index + 1}`"
                class="w-full h-full object-cover"
              />
            </div>
          </div>

          <div class="mt-4 p-4 bg-muted rounded-lg">
            <p class="text-sm font-medium mb-1">Prompt:</p>
            <p class="text-sm text-muted-foreground">{{ currentJob.prompt }}</p>
            <p v-if="currentJob.optimized_prompt" class="text-sm font-medium mt-2 mb-1">Optimized:</p>
            <p v-if="currentJob.optimized_prompt" class="text-sm text-muted-foreground">{{ currentJob.optimized_prompt }}</p>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'
import { Wand2, User, Image, X } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { charactersApi, inferenceApi, type Character, type InferenceJob } from '@/services/api'

const route = useRoute()
const toast = useToast()

const form = ref({
  character_id: '',
  prompt: '',
  lora_weight: 0.73,
  test_dim: 1024,
  do_optimize_prompt: true,
  batch_size: 4,
  num_inference_steps: 30,
  fix_outfit: false,
  safety_check: true,
  face_enhance: false
})

const availableCharacters = ref<Character[]>([])
const recentJobs = ref<InferenceJob[]>([])
const currentJob = ref<InferenceJob | null>(null)
const showResults = ref(false)
const isGenerating = ref(false)

const selectedCharacter = computed(() =>
  availableCharacters.value.find(c => c.id.toString() === form.value.character_id)
)

const canGenerate = computed(() =>
  form.value.character_id && form.value.prompt.trim()
)

const loadAvailableCharacters = async () => {
  try {
    availableCharacters.value = await charactersApi.getAvailable()

    // Auto-select character from URL parameter
    const characterParam = route.query.character
    if (characterParam) {
      form.value.character_id = characterParam.toString()
    }
  } catch (error: any) {
    toast.error('Failed to load available characters')
  }
}

const loadRecentJobs = async () => {
  try {
    recentJobs.value = await inferenceApi.listJobs()
  } catch (error: any) {
    toast.error('Failed to load recent generations')
  }
}

const generateImages = async () => {
  if (!canGenerate.value) return

  isGenerating.value = true
  try {
    const job = await inferenceApi.generate({
      character_id: parseInt(form.value.character_id),
      prompt: form.value.prompt,
      lora_weight: form.value.lora_weight,
      test_dim: form.value.test_dim,
      do_optimize_prompt: form.value.do_optimize_prompt,
      batch_size: form.value.batch_size,
      num_inference_steps: form.value.num_inference_steps,
      fix_outfit: form.value.fix_outfit,
      safety_check: form.value.safety_check,
      face_enhance: form.value.face_enhance
    })

    currentJob.value = job
    showResults.value = true
    recentJobs.value.unshift(job)

    toast.success('Image generation started!')

    // Poll for completion (in a real app, you'd use WebSocket)
    pollJobStatus(job.id)
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to start generation')
  } finally {
    isGenerating.value = false
  }
}

const pollJobStatus = async (jobId: number) => {
  const poll = async () => {
    try {
      const job = await inferenceApi.getJob(jobId)
      if (currentJob.value?.id === jobId) {
        currentJob.value = job
      }

      // Update in recent jobs list
      const index = recentJobs.value.findIndex(j => j.id === jobId)
      if (index !== -1) {
        recentJobs.value[index] = job
      }

      if (job.status === 'running' || job.status === 'pending') {
        setTimeout(poll, 2000) // Poll every 2 seconds
      }
    } catch (error) {
      console.error('Failed to poll job status:', error)
    }
  }

  poll()
}

const viewJob = (job: InferenceJob) => {
  currentJob.value = job
  showResults.value = true
}

const applyPreset = (preset: string) => {
  const presets = {
    portrait: {
      prompt: 'portrait, looking at camera, detailed face, professional lighting, high quality',
      test_dim: 1024,
      lora_weight: 0.75
    },
    landscape: {
      prompt: 'full body, standing in a beautiful landscape, detailed background, cinematic lighting',
      test_dim: 1024,
      lora_weight: 0.7
    },
    action: {
      prompt: 'dynamic action pose, dramatic lighting, detailed, high energy',
      test_dim: 1024,
      lora_weight: 0.8
    }
  }

  const config = presets[preset as keyof typeof presets]
  if (config) {
    Object.assign(form.value, config)
    toast.info(`Applied ${preset} preset`)
  }
}

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadAvailableCharacters()
  loadRecentJobs()
})
</script>
