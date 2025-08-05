<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Datasets</h1>
          <p class="text-muted-foreground">
            Manage your character training datasets
          </p>
        </div>
        <Button @click="$router.push('/media')" data-tour="create-dataset">
          <FolderPlus class="mr-2 h-4 w-4" />
          Create Dataset
        </Button>
      </div>

      <!-- Datasets Grid -->
      <div v-if="datasets.length > 0" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="dataset in datasets"
          :key="dataset.id"
          class="p-6 hover:shadow-lg transition-shadow cursor-pointer"
          @click="viewDataset(dataset)"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Database class="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 class="font-semibold text-lg">{{ dataset.name }}</h3>
                <p class="text-sm text-muted-foreground">{{ dataset.image_count }} images</p>
              </div>
            </div>
            <StatusBadge :status="dataset.status" />
          </div>

          <div class="space-y-2 mb-4">
            <div class="flex items-center text-sm">
              <Tag class="mr-2 h-4 w-4 text-muted-foreground" />
              <span class="font-medium">Trigger:</span>
              <span class="ml-1 text-muted-foreground">{{ dataset.trigger_word }}</span>
            </div>
            <div class="flex items-center text-sm">
              <Calendar class="mr-2 h-4 w-4 text-muted-foreground" />
              <span class="text-muted-foreground">{{ formatDate(dataset.created_at) }}</span>
            </div>
          </div>

          <div class="flex justify-between items-center">
            <div class="flex space-x-2">
              <Button
                @click.stop="editDataset(dataset)"
                variant="outline"
                size="sm"
              >
                <Edit class="mr-1 h-3 w-3" />
                Edit
              </Button>
              <Button
                @click.stop="deleteDataset(dataset)"
                variant="outline"
                size="sm"
                class="text-destructive hover:text-destructive"
              >
                <Trash2 class="mr-1 h-3 w-3" />
                Delete
              </Button>
            </div>
            <Button
              v-if="dataset.status === 'ready'"
              @click.stop="useForTraining(dataset)"
              size="sm"
            >
              <Zap class="mr-1 h-3 w-3" />
              Train
            </Button>
          </div>
        </Card>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-12">
        <Database class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h3 class="text-lg font-semibold mb-2">No datasets yet</h3>
        <p class="text-muted-foreground mb-6">
          Create your first dataset to start training character LoRAs
        </p>
        <Button @click="$router.push('/media')">
          <FolderPlus class="mr-2 h-4 w-4" />
          Create Your First Dataset
        </Button>
      </div>

      <!-- Dataset Detail Modal -->
      <DatasetDetailModal
        v-if="selectedDataset"
        :dataset="selectedDataset"
        @close="selectedDataset = null"
        @updated="loadDatasets"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  FolderPlus, Database, Tag, Calendar, Edit, Trash2, Zap
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import DatasetDetailModal from '@/components/datasets/DatasetDetailModal.vue'
import { datasetApi, type Dataset } from '@/services/api'

const router = useRouter()
const toast = useToast()

const datasets = ref<Dataset[]>([])
const selectedDataset = ref<Dataset | null>(null)
const isLoading = ref(false)

const loadDatasets = async () => {
  isLoading.value = true
  try {
    const response = await datasetApi.getDatasets()
    datasets.value = response.datasets
  } catch (error) {
    toast.error('Failed to load datasets')
  } finally {
    isLoading.value = false
  }
}

const viewDataset = (dataset: Dataset) => {
  selectedDataset.value = dataset
}

const editDataset = (dataset: Dataset) => {
  selectedDataset.value = dataset
}

const deleteDataset = async (dataset: Dataset) => {
  if (!confirm(`Are you sure you want to delete the dataset "${dataset.name}"?`)) {
    return
  }

  try {
    await datasetApi.deleteDataset(dataset.id)
    toast.success('Dataset deleted successfully')
    loadDatasets()
  } catch (error) {
    toast.error('Failed to delete dataset')
  }
}

const useForTraining = (dataset: Dataset) => {
  // Navigate to character creation with dataset pre-selected
  router.push({
    path: '/characters/create',
    query: { dataset: dataset.id }
  })
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(() => {
  loadDatasets()
})
</script>
