<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Create Character</h1>
        <p class="text-muted-foreground">
          Create a new AI character for LoRA training
        </p>
      </div>

      <form @submit.prevent="createCharacter" class="space-y-6">
        <!-- Character Details -->
        <Card class="p-6">
          <h3 class="text-lg font-semibold mb-4">Character Details</h3>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2">Character Name</label>
              <Input
                v-model="form.name"
                placeholder="Enter character name (e.g., 'anime_girl', 'fantasy_warrior')"
                required
                pattern="[a-zA-Z0-9_-]+"
                title="Only letters, numbers, underscores, and hyphens allowed"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Use only letters, numbers, underscores, and hyphens. This will be used for file naming.
              </p>
            </div>
          </div>
        </Card>

        <!-- Reference Image -->
        <Card class="p-6">
          <h3 class="text-lg font-semibold mb-4">Reference Image</h3>

          <div class="space-y-4">
            <!-- Image Selection -->
            <div v-if="!selectedImage">
              <div class="grid gap-4">
                <!-- Upload New Image -->
                <div
                  @drop="handleDrop"
                  @dragover.prevent
                  @dragenter.prevent
                  class="border-2 border-dashed border-border rounded-lg p-6 text-center transition-colors cursor-pointer hover:border-primary"
                  @click="triggerFileUpload"
                >
                  <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    @change="handleFileSelect"
                    class="hidden"
                  />

                  <Upload class="mx-auto h-8 w-8 text-muted-foreground mb-2" />
                  <p class="font-medium">Upload Reference Image</p>
                  <p class="text-sm text-muted-foreground">
                    Drop an image here or click to browse
                  </p>
                </div>

                <!-- Or Select from Media Library -->
                <div class="text-center">
                  <p class="text-sm text-muted-foreground mb-3">Or select from your media library</p>
                  <Button type="button" variant="outline" @click="showMediaLibrary = true">
                    <Image class="mr-2 h-4 w-4" />
                    Choose from Library
                  </Button>
                </div>
              </div>
            </div>

            <!-- Selected Image Preview -->
            <div v-else class="space-y-4">
              <div class="relative inline-block">
                <img
                  :src="selectedImage.file_url || selectedImage.preview"
                  :alt="selectedImage.original_filename || selectedImage.name"
                  class="w-48 h-48 object-cover rounded-lg border"
                />
                <Button
                  @click="selectedImage = null"
                  class="absolute -top-2 -right-2"
                  size="sm"
                  variant="destructive"
                >
                  <X class="h-3 w-3" />
                </Button>
              </div>
              <div>
                <p class="font-medium">{{ selectedImage.original_filename || selectedImage.name }}</p>
                <p class="text-sm text-muted-foreground">
                  {{ selectedImage.width }}×{{ selectedImage.height }}
                  {{ selectedImage.file_size ? `• ${formatFileSize(selectedImage.file_size)}` : '' }}
                </p>
              </div>
            </div>
          </div>
        </Card>

        <!-- Training Configuration -->
        <Card class="p-6">
          <h3 class="text-lg font-semibold mb-4">Training Configuration</h3>

          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="block text-sm font-medium mb-2">Training Steps</label>
              <Input
                v-model.number="form.steps"
                type="number"
                min="100"
                max="5000"
                step="100"
              />
              <p class="text-xs text-muted-foreground mt-1">
                More steps = better quality but longer training time (recommended: 800)
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">Learning Rate</label>
              <Input
                v-model.number="form.learning_rate"
                type="number"
                min="0.0001"
                max="0.01"
                step="0.0001"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Lower = more stable training (recommended: 0.0008)
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">Training Dimension</label>
              <select v-model="form.train_dim" class="w-full h-10 px-3 py-2 border border-input rounded-md bg-background">
                <option value="512">512x512 (Faster)</option>
                <option value="768">768x768 (Balanced)</option>
                <option value="1024">1024x1024 (Higher Quality)</option>
              </select>
              <p class="text-xs text-muted-foreground mt-1">
                Higher resolution = better quality but slower training
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">LoRA Rank</label>
              <Input
                v-model.number="form.rank_dim"
                type="number"
                min="4"
                max="32"
                step="4"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Higher rank = more detailed but larger model (recommended: 8)
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">Batch Size</label>
              <Input
                v-model.number="form.batch_size"
                type="number"
                min="1"
                max="4"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Higher batch size requires more VRAM
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">PuLID-Flux Images</label>
              <Input
                v-model.number="form.pulidflux_images"
                type="number"
                min="0"
                max="10"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Additional synthetic images for training (0 = disabled)
              </p>
            </div>
          </div>
        </Card>

        <!-- Actions -->
        <div class="flex justify-end space-x-3">
          <Button type="button" variant="outline" @click="$router.push('/characters')">
            Cancel
          </Button>
          <Button type="submit" :disabled="!canCreate || isCreating">
            <Zap class="mr-2 h-4 w-4" />
            {{ isCreating ? 'Creating...' : 'Create Character' }}
          </Button>
        </div>
      </form>
    </div>

    <!-- Media Library Modal -->
    <div
      v-if="showMediaLibrary"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="showMediaLibrary = false"
    >
      <div
        class="bg-background rounded-lg max-w-4xl max-h-[80vh] overflow-auto w-full"
        @click.stop
      >
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Select Reference Image</h3>
            <Button @click="showMediaLibrary = false" variant="ghost" size="sm">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div v-if="mediaFiles.length === 0" class="text-center py-8">
            <p class="text-muted-foreground">No images in your media library</p>
            <Button @click="showMediaLibrary = false; $router.push('/media')" class="mt-2">
              Upload Images
            </Button>
          </div>

          <div v-else class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div
              v-for="file in mediaFiles"
              :key="file.filename"
              class="aspect-square bg-muted rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
              @click="selectImageFromLibrary(file)"
            >
              <img
                :src="file.file_url"
                :alt="file.original_filename"
                class="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { Upload, Image, X, Zap } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { charactersApi, mediaApi, type MediaFile } from '@/services/api'

const router = useRouter()
const toast = useToast()

const form = ref({
  name: '',
  steps: 800,
  batch_size: 1,
  learning_rate: 0.0008,
  train_dim: 512,
  rank_dim: 8,
  pulidflux_images: 0
})

const selectedImage = ref<MediaFile | File | null>(null)
const showMediaLibrary = ref(false)
const mediaFiles = ref<MediaFile[]>([])
const isCreating = ref(false)
const fileInput = ref<HTMLInputElement>()

const canCreate = computed(() => {
  return form.value.name.trim() && selectedImage.value
})

const loadMediaFiles = async () => {
  try {
    const response = await mediaApi.list()
    mediaFiles.value = response.files
  } catch (error) {
    console.error('Failed to load media files:', error)
  }
}

const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    // Create preview URL for the file
    const preview = URL.createObjectURL(file)
    selectedImage.value = Object.assign(file, { preview })
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0]
    const preview = URL.createObjectURL(file)
    selectedImage.value = Object.assign(file, { preview })
  }
}

const selectImageFromLibrary = (file: MediaFile) => {
  selectedImage.value = file
  showMediaLibrary.value = false
}

const createCharacter = async () => {
  if (!canCreate.value) return

  isCreating.value = true
  try {
    let imagePath = ''

    // If selected image is a File (newly uploaded), upload it first
    if (selectedImage.value instanceof File) {
      const uploadedFile = await mediaApi.upload(selectedImage.value)
      imagePath = uploadedFile.file_path
    } else {
      // Use existing media file path
      imagePath = (selectedImage.value as MediaFile).file_path
    }

    // Create character
    const character = await charactersApi.create({
      name: form.value.name,
      input_image_path: imagePath
    })

    toast.success('Character created successfully!')
    router.push(`/characters/${character.id}`)
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to create character')
  } finally {
    isCreating.value = false
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadMediaFiles()
})
</script>
