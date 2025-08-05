<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-background rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
      <div class="p-6 border-b border-border">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold">{{ dataset.name }}</h2>
            <div class="flex items-center space-x-4 mt-2">
              <StatusBadge :status="dataset.status" />
              <span class="text-sm text-muted-foreground">
                {{ dataset.image_count }} images
              </span>
              <span class="text-sm text-muted-foreground">
                Created {{ formatDate(dataset.created_at) }}
              </span>
            </div>
          </div>
          <Button @click="$emit('close')" variant="ghost" size="sm">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div class="p-6 overflow-auto max-h-[calc(90vh-200px)]">
        <div class="grid lg:grid-cols-3 gap-6">
          <!-- Dataset Configuration -->
          <div class="lg:col-span-1 space-y-6">
            <div>
              <h3 class="text-lg font-semibold mb-4">Configuration</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium mb-2">Trigger Word</label>
                  <div class="flex space-x-2">
                    <Input
                      v-model="editableTriggerWord"
                      class="flex-1"
                      :disabled="!isEditing"
                    />
                    <Button
                      @click="toggleTriggerEdit"
                      variant="outline"
                      size="sm"
                    >
                      <Edit class="h-4 w-4" />
                    </Button>
                  </div>
                  <Button
                    v-if="isEditing && triggerWordChanged"
                    @click="saveTriggerWord"
                    size="sm"
                    class="mt-2"
                    :loading="isSaving"
                  >
                    Save Changes
                  </Button>
                </div>

                <div>
                  <label class="block text-sm font-medium mb-2">Caption Template</label>
                  <textarea
                    :value="dataset.caption_template"
                    readonly
                    class="w-full min-h-[80px] px-3 py-2 border border-input rounded-md resize-none bg-muted"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div class="flex items-center space-x-2">
                    <Check v-if="dataset.auto_caption" class="h-4 w-4 text-green-500" />
                    <X v-else class="h-4 w-4 text-red-500" />
                    <span>Auto Caption</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <Check v-if="dataset.resize_images" class="h-4 w-4 text-green-500" />
                    <X v-else class="h-4 w-4 text-red-500" />
                    <span>Resize Images</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <Check v-if="dataset.crop_images" class="h-4 w-4 text-green-500" />
                    <X v-else class="h-4 w-4 text-red-500" />
                    <span>Crop Images</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <Check v-if="dataset.flip_images" class="h-4 w-4 text-green-500" />
                    <X v-else class="h-4 w-4 text-red-500" />
                    <span>Flip Images</span>
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium mb-1">Quality Filter</label>
                  <span class="text-sm text-muted-foreground capitalize">{{ dataset.quality_filter }}</span>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="space-y-2">
              <Button
                v-if="dataset.status === 'ready'"
                @click="useForTraining"
                class="w-full"
              >
                <Zap class="mr-2 h-4 w-4" />
                Use for Training
              </Button>
              <Button
                @click="downloadDataset"
                variant="outline"
                class="w-full"
              >
                <Download class="mr-2 h-4 w-4" />
                Download Dataset
              </Button>
            </div>
          </div>

          <!-- Images Grid -->
          <div class="lg:col-span-2">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">Images & Captions</h3>
              <div class="flex items-center space-x-2">
                <Button
                  @click="regenerateCaptions"
                  variant="outline"
                  size="sm"
                  :loading="isRegenerating"
                >
                  <RefreshCw class="mr-2 h-4 w-4" />
                  Regenerate Captions
                </Button>
              </div>
            </div>

            <div v-if="images.length > 0" class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div
                v-for="image in images"
                :key="image.id"
                class="space-y-2"
              >
                <div class="aspect-square rounded-lg overflow-hidden border border-border">
                  <img
                    :src="`/api/media/files/${image.filename}`"
                    :alt="image.original_filename"
                    class="w-full h-full object-cover"
                  />
                </div>
                
                <div>
                  <p class="text-xs text-muted-foreground truncate">
                    {{ image.original_filename }}
                  </p>
                  <textarea
                    v-model="image.caption"
                    @blur="updateCaption(image)"
                    placeholder="Enter caption..."
                    class="w-full mt-1 px-2 py-1 text-xs border border-input rounded resize-none"
                    rows="2"
                  />
                </div>
              </div>
            </div>

            <div v-else class="text-center py-8">
              <Image class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p class="text-muted-foreground">No images found in this dataset</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  X, Edit, Check, Zap, Download, RefreshCw, Image
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { datasetApi, type Dataset, type DatasetImage } from '@/services/api'

interface Props {
  dataset: Dataset
}

interface Emits {
  (e: 'close'): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const router = useRouter()
const toast = useToast()

const images = ref<DatasetImage[]>([])
const isEditing = ref(false)
const isSaving = ref(false)
const isRegenerating = ref(false)
const editableTriggerWord = ref(props.dataset.trigger_word)

const triggerWordChanged = computed(() => {
  return editableTriggerWord.value !== props.dataset.trigger_word
})

const loadImages = async () => {
  try {
    images.value = await datasetApi.getDatasetImages(props.dataset.id)
  } catch (error) {
    toast.error('Failed to load dataset images')
  }
}

const toggleTriggerEdit = () => {
  if (isEditing.value && triggerWordChanged.value) {
    // Ask for confirmation if there are unsaved changes
    if (confirm('You have unsaved changes. Do you want to discard them?')) {
      editableTriggerWord.value = props.dataset.trigger_word
      isEditing.value = false
    }
  } else {
    isEditing.value = !isEditing.value
  }
}

const saveTriggerWord = async () => {
  if (!editableTriggerWord.value.trim()) {
    toast.error('Trigger word cannot be empty')
    return
  }

  isSaving.value = true
  try {
    await datasetApi.updateTriggerWord(props.dataset.id, editableTriggerWord.value.trim())
    toast.success('Trigger word updated successfully')
    isEditing.value = false
    emit('updated')
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Failed to update trigger word'
    toast.error(message)
  } finally {
    isSaving.value = false
  }
}

const updateCaption = async (image: DatasetImage) => {
  try {
    await datasetApi.updateImageCaption(props.dataset.id, image.id, image.caption || '')
    toast.success('Caption updated')
  } catch (error) {
    toast.error('Failed to update caption')
  }
}

const useForTraining = () => {
  router.push({
    path: '/characters/create',
    query: { dataset: props.dataset.id }
  })
  emit('close')
}

const downloadDataset = () => {
  // TODO: Implement dataset download
  toast.info('Dataset download feature coming soon')
}

const regenerateCaptions = async () => {
  isRegenerating.value = true
  try {
    // TODO: Implement caption regeneration API
    toast.info('Caption regeneration feature coming soon')
  } catch (error) {
    toast.error('Failed to regenerate captions')
  } finally {
    isRegenerating.value = false
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(() => {
  loadImages()
})
</script>
