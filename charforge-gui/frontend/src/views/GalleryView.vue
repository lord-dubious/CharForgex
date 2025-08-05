<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Gallery</h1>
          <p class="text-muted-foreground">
            Browse and manage your generated images
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <Button @click="viewMode = 'grid'" :variant="viewMode === 'grid' ? 'default' : 'outline'" size="sm">
            <Grid3X3 class="h-4 w-4" />
          </Button>
          <Button @click="viewMode = 'masonry'" :variant="viewMode === 'masonry' ? 'default' : 'outline'" size="sm">
            <LayoutGrid class="h-4 w-4" />
          </Button>
          <Button @click="viewMode = 'list'" :variant="viewMode === 'list' ? 'default' : 'outline'" size="sm">
            <List class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <!-- Filters -->
      <Card class="p-4">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium">Character:</label>
            <select
              v-model="filters.character"
              class="h-8 px-2 py-1 border border-input rounded bg-background text-sm"
            >
              <option value="">All Characters</option>
              <option
                v-for="character in availableCharacters"
                :key="character.id"
                :value="character.id"
              >
                {{ character.name }}
              </option>
            </select>
          </div>

          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium">Status:</label>
            <select
              v-model="filters.status"
              class="h-8 px-2 py-1 border border-input rounded bg-background text-sm"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium">Sort:</label>
            <select
              v-model="filters.sort"
              class="h-8 px-2 py-1 border border-input rounded bg-background text-sm"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="character">By Character</option>
            </select>
          </div>

          <Button @click="clearFilters" variant="outline" size="sm">
            Clear Filters
          </Button>
        </div>
      </Card>

      <!-- Gallery Content -->
      <div v-if="filteredJobs.length > 0">
        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <div
            v-for="job in filteredJobs"
            :key="job.id"
            class="group relative aspect-square bg-muted rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
            @click="selectedJob = job"
          >
            <img
              v-if="job.output_paths && job.output_paths[0]"
              :src="job.output_paths[0]"
              :alt="job.prompt"
              class="w-full h-full object-cover"
              loading="lazy"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <Image class="h-8 w-8 text-muted-foreground" />
            </div>

            <!-- Overlay -->
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />

            <!-- Status Badge -->
            <div class="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <StatusBadge :status="job.status" />
            </div>

            <!-- Actions -->
            <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button @click.stop="downloadImages(job)" size="sm" variant="secondary">
                <Download class="h-3 w-3" />
              </Button>
            </div>

            <!-- Info -->
            <div class="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <p class="text-white text-xs font-medium truncate">{{ job.character_name }}</p>
              <p class="text-white/80 text-xs truncate">{{ job.prompt }}</p>
            </div>
          </div>
        </div>

        <!-- Masonry View -->
        <div v-else-if="viewMode === 'masonry'" class="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
          <div
            v-for="job in filteredJobs"
            :key="job.id"
            class="break-inside-avoid group relative bg-muted rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
            @click="selectedJob = job"
          >
            <img
              v-if="job.output_paths && job.output_paths[0]"
              :src="job.output_paths[0]"
              :alt="job.prompt"
              class="w-full object-cover"
              loading="lazy"
            />
            <div v-else class="w-full aspect-square flex items-center justify-center">
              <Image class="h-8 w-8 text-muted-foreground" />
            </div>

            <div class="p-3">
              <p class="font-medium text-sm truncate">{{ job.character_name }}</p>
              <p class="text-xs text-muted-foreground truncate">{{ job.prompt }}</p>
              <div class="flex items-center justify-between mt-2">
                <StatusBadge :status="job.status" />
                <span class="text-xs text-muted-foreground">{{ formatDate(job.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- List View -->
        <div v-else class="space-y-3">
          <Card
            v-for="job in filteredJobs"
            :key="job.id"
            class="p-4 cursor-pointer hover:bg-accent transition-colors"
            @click="selectedJob = job"
          >
            <div class="flex items-center space-x-4">
              <!-- Thumbnail -->
              <div class="w-16 h-16 bg-muted rounded overflow-hidden flex-shrink-0">
                <img
                  v-if="job.output_paths && job.output_paths[0]"
                  :src="job.output_paths[0]"
                  :alt="job.prompt"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <Image class="h-6 w-6 text-muted-foreground" />
                </div>
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center space-x-2 mb-1">
                  <h4 class="font-medium">{{ job.character_name }}</h4>
                  <StatusBadge :status="job.status" />
                </div>
                <p class="text-sm text-muted-foreground truncate">{{ job.prompt }}</p>
                <div class="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                  <span>{{ formatDate(job.created_at) }}</span>
                  <span>{{ job.batch_size }} images</span>
                  <span>{{ job.test_dim }}×{{ job.test_dim }}</span>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center space-x-2">
                <Button @click.stop="downloadImages(job)" variant="outline" size="sm">
                  <Download class="mr-2 h-3 w-3" />
                  Download
                </Button>
                <Button @click.stop="regenerateImages(job)" variant="outline" size="sm">
                  <RefreshCw class="mr-2 h-3 w-3" />
                  Regenerate
                </Button>
              </div>
            </div>
          </Card>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-center space-x-2">
          <Button
            @click="currentPage--"
            :disabled="currentPage === 1"
            variant="outline"
            size="sm"
          >
            Previous
          </Button>
          <span class="flex items-center px-3 text-sm">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          <Button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            variant="outline"
            size="sm"
          >
            Next
          </Button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!isLoading" class="text-center py-12">
        <div class="mx-auto w-16 h-16 bg-muted rounded-lg flex items-center justify-center mb-4">
          <Image class="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 class="text-lg font-semibold mb-2">No images generated yet</h3>
        <p class="text-muted-foreground mb-4">
          Start generating images with your trained characters
        </p>
        <Button @click="$router.push('/inference')">
          <Wand2 class="mr-2 h-4 w-4" />
          Generate Images
        </Button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-muted-foreground">Loading gallery...</p>
      </div>
    </div>

    <!-- Image Detail Modal -->
    <div
      v-if="selectedJob"
      class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      @click="selectedJob = null"
    >
      <div
        class="bg-background rounded-lg max-w-6xl w-full max-h-[90vh] overflow-auto"
        @click.stop
      >
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h3 class="text-lg font-semibold">{{ selectedJob.character_name }}</h3>
              <p class="text-sm text-muted-foreground">
                Generated {{ formatDate(selectedJob.created_at) }}
              </p>
            </div>
            <Button @click="selectedJob = null" variant="ghost" size="sm">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Images Grid -->
          <div v-if="selectedJob.output_paths" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div
              v-for="(imagePath, index) in selectedJob.output_paths"
              :key="index"
              class="aspect-square bg-muted rounded-lg overflow-hidden"
            >
              <img
                :src="imagePath"
                :alt="`Generated image ${index + 1}`"
                class="w-full h-full object-cover cursor-pointer"
                @click="openImageFullscreen(imagePath)"
              />
            </div>
          </div>

          <!-- Job Details -->
          <div class="space-y-4">
            <div class="p-4 bg-muted rounded-lg">
              <h4 class="font-medium mb-2">Prompt</h4>
              <p class="text-sm">{{ selectedJob.prompt }}</p>
              <div v-if="selectedJob.optimized_prompt" class="mt-2">
                <h4 class="font-medium mb-1">Optimized Prompt</h4>
                <p class="text-sm text-muted-foreground">{{ selectedJob.optimized_prompt }}</p>
              </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p class="text-muted-foreground">Status</p>
                <StatusBadge :status="selectedJob.status" />
              </div>
              <div>
                <p class="text-muted-foreground">LoRA Weight</p>
                <p class="font-medium">{{ selectedJob.lora_weight }}</p>
              </div>
              <div>
                <p class="text-muted-foreground">Dimensions</p>
                <p class="font-medium">{{ selectedJob.test_dim }}×{{ selectedJob.test_dim }}</p>
              </div>
              <div>
                <p class="text-muted-foreground">Batch Size</p>
                <p class="font-medium">{{ selectedJob.batch_size }}</p>
              </div>
            </div>

            <div class="flex justify-end space-x-2">
              <Button @click="downloadImages(selectedJob)" variant="outline">
                <Download class="mr-2 h-4 w-4" />
                Download All
              </Button>
              <Button @click="regenerateImages(selectedJob)" variant="outline">
                <RefreshCw class="mr-2 h-4 w-4" />
                Regenerate
              </Button>
              <Button @click="shareJob(selectedJob)">
                <Share class="mr-2 h-4 w-4" />
                Share
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  Grid3X3, LayoutGrid, List, Image, Download, RefreshCw, Share, X, Wand2
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { inferenceApi, charactersApi, type InferenceJob, type Character } from '@/services/api'

const router = useRouter()
const toast = useToast()

const jobs = ref<InferenceJob[]>([])
const availableCharacters = ref<Character[]>([])
const selectedJob = ref<InferenceJob | null>(null)
const viewMode = ref<'grid' | 'masonry' | 'list'>('grid')
const isLoading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 24

const filters = ref({
  character: '',
  status: '',
  sort: 'newest'
})

const filteredJobs = computed(() => {
  let filtered = [...jobs.value]

  // Apply filters
  if (filters.value.character) {
    filtered = filtered.filter(job => job.character_id.toString() === filters.value.character)
  }

  if (filters.value.status) {
    filtered = filtered.filter(job => job.status === filters.value.status)
  }

  // Apply sorting
  filtered.sort((a, b) => {
    switch (filters.value.sort) {
      case 'newest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      case 'oldest':
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      case 'character':
        return a.character_name.localeCompare(b.character_name)
      default:
        return 0
    }
  })

  // Apply pagination
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filtered.slice(start, end)
})

const totalPages = computed(() => {
  let filtered = [...jobs.value]

  if (filters.value.character) {
    filtered = filtered.filter(job => job.character_id.toString() === filters.value.character)
  }

  if (filters.value.status) {
    filtered = filtered.filter(job => job.status === filters.value.status)
  }

  return Math.ceil(filtered.length / itemsPerPage)
})

const loadJobs = async () => {
  isLoading.value = true
  try {
    jobs.value = await inferenceApi.listJobs(undefined, 1000) // Load more items for gallery
  } catch (error: any) {
    toast.error('Failed to load gallery')
  } finally {
    isLoading.value = false
  }
}

const loadCharacters = async () => {
  try {
    availableCharacters.value = await charactersApi.getAvailable()
  } catch (error) {
    console.error('Failed to load characters:', error)
  }
}

const clearFilters = () => {
  filters.value = {
    character: '',
    status: '',
    sort: 'newest'
  }
  currentPage.value = 1
}

const downloadImages = (job: InferenceJob) => {
  if (!job.output_paths) return

  job.output_paths.forEach((imagePath, index) => {
    const link = document.createElement('a')
    link.href = imagePath
    link.download = `${job.character_name}_${job.id}_${index + 1}.jpg`
    link.click()
  })

  toast.success('Download started!')
}

const regenerateImages = (job: InferenceJob) => {
  router.push({
    path: '/inference',
    query: {
      character: job.character_id.toString(),
      prompt: job.prompt,
      lora_weight: job.lora_weight.toString(),
      test_dim: job.test_dim.toString(),
      batch_size: job.batch_size.toString()
    }
  })
}

const shareJob = (job: InferenceJob) => {
  const url = `${window.location.origin}/gallery?job=${job.id}`
  navigator.clipboard.writeText(url)
  toast.success('Share link copied to clipboard!')
}

const openImageFullscreen = (imagePath: string) => {
  window.open(imagePath, '_blank')
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

// Reset page when filters change
watch(filters, () => {
  currentPage.value = 1
}, { deep: true })

onMounted(() => {
  loadJobs()
  loadCharacters()
})
</script>
