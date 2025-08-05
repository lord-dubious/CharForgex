<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Characters</h1>
          <p class="text-muted-foreground">
            Manage your AI characters and their training status
          </p>
        </div>
        <Button @click="$router.push('/characters/create')" data-tour="create-character">
          <Plus class="mr-2 h-4 w-4" />
          Create Character
        </Button>
      </div>

      <!-- Characters Grid -->
      <div v-if="characters.length > 0" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card
          v-for="character in characters"
          :key="character.id"
          class="p-6 cursor-pointer hover:shadow-lg transition-shadow"
          @click="$router.push(`/characters/${character.id}`)"
        >
          <div class="space-y-4">
            <!-- Character Header -->
            <div class="flex items-start justify-between">
              <div>
                <h3 class="text-lg font-semibold">{{ character.name }}</h3>
                <p class="text-sm text-muted-foreground">
                  Created {{ formatDate(character.created_at) }}
                </p>
              </div>
              <div class="flex items-center space-x-2">
                <StatusBadge :status="character.status" />
                <Button
                  @click.stop="showCharacterMenu(character)"
                  variant="ghost"
                  size="sm"
                >
                  <MoreVertical class="h-4 w-4" />
                </Button>
              </div>
            </div>

            <!-- Character Preview -->
            <div class="aspect-square bg-muted rounded-lg overflow-hidden">
              <img
                v-if="character.preview_image"
                :src="character.preview_image"
                :alt="character.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <User class="h-12 w-12 text-muted-foreground" />
              </div>
            </div>

            <!-- Character Stats -->
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p class="text-muted-foreground">Status</p>
                <p class="font-medium capitalize">{{ character.status }}</p>
              </div>
              <div>
                <p class="text-muted-foreground">Training</p>
                <p class="font-medium">
                  {{ character.status === 'completed' ? 'Complete' : 'Pending' }}
                </p>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex space-x-2">
              <Button
                v-if="character.status === 'completed'"
                @click.stop="$router.push(`/inference?character=${character.id}`)"
                size="sm"
                class="flex-1"
              >
                <Wand2 class="mr-2 h-3 w-3" />
                Generate
              </Button>
              <Button
                v-else-if="character.status === 'created'"
                @click.stop="startTraining(character)"
                size="sm"
                class="flex-1"
              >
                <Zap class="mr-2 h-3 w-3" />
                Start Training
              </Button>
              <Button
                v-else
                @click.stop="$router.push(`/training?character=${character.id}`)"
                size="sm"
                variant="outline"
                class="flex-1"
              >
                <Eye class="mr-2 h-3 w-3" />
                View Progress
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <!-- Empty State -->
      <div v-else-if="!isLoading" class="text-center py-12">
        <div class="mx-auto w-16 h-16 bg-muted rounded-lg flex items-center justify-center mb-4">
          <Users class="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 class="text-lg font-semibold mb-2">No characters yet</h3>
        <p class="text-muted-foreground mb-4">
          Create your first AI character to get started with LoRA training
        </p>
        <Button @click="$router.push('/characters/create')">
          <Plus class="mr-2 h-4 w-4" />
          Create Your First Character
        </Button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-muted-foreground">Loading characters...</p>
      </div>
    </div>

    <!-- Character Menu Modal -->
    <div
      v-if="selectedCharacter"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="selectedCharacter = null"
    >
      <div
        class="bg-background rounded-lg p-6 min-w-[300px]"
        @click.stop
      >
        <h3 class="text-lg font-semibold mb-4">{{ selectedCharacter.name }}</h3>

        <div class="space-y-2">
          <Button
            @click="$router.push(`/characters/${selectedCharacter.id}`)"
            variant="ghost"
            class="w-full justify-start"
          >
            <Eye class="mr-2 h-4 w-4" />
            View Details
          </Button>

          <Button
            v-if="selectedCharacter.status === 'completed'"
            @click="$router.push(`/inference?character=${selectedCharacter.id}`)"
            variant="ghost"
            class="w-full justify-start"
          >
            <Wand2 class="mr-2 h-4 w-4" />
            Generate Images
          </Button>

          <Button
            @click="duplicateCharacter(selectedCharacter)"
            variant="ghost"
            class="w-full justify-start"
          >
            <Copy class="mr-2 h-4 w-4" />
            Duplicate
          </Button>

          <Button
            @click="deleteCharacter(selectedCharacter)"
            variant="ghost"
            class="w-full justify-start text-destructive hover:text-destructive"
          >
            <Trash2 class="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>

        <div class="mt-4 pt-4 border-t">
          <Button @click="selectedCharacter = null" variant="outline" class="w-full">
            Cancel
          </Button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import {
  Plus, User, Users, MoreVertical, Wand2, Zap, Eye, Copy, Trash2
} from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { charactersApi, trainingApi, type Character } from '@/services/api'

const router = useRouter()
const toast = useToast()

const characters = ref<Character[]>([])
const selectedCharacter = ref<Character | null>(null)
const isLoading = ref(false)

const loadCharacters = async () => {
  isLoading.value = true
  try {
    characters.value = await charactersApi.list()
  } catch (error: any) {
    toast.error('Failed to load characters')
  } finally {
    isLoading.value = false
  }
}

const showCharacterMenu = (character: Character) => {
  selectedCharacter.value = character
}

const startTraining = async (character: Character) => {
  try {
    await trainingApi.startTraining(character.id, {
      steps: 800,
      batch_size: 1,
      learning_rate: 0.0008,
      train_dim: 512,
      rank_dim: 8,
      pulidflux_images: 0
    })

    toast.success('Training started successfully!')
    character.status = 'training'
    router.push(`/training?character=${character.id}`)
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to start training')
  }
}

const duplicateCharacter = async (character: Character) => {
  try {
    const newCharacter = await charactersApi.create({
      name: `${character.name}_copy`,
      input_image_path: character.input_image_path
    })

    characters.value.unshift(newCharacter)
    selectedCharacter.value = null
    toast.success('Character duplicated successfully!')
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to duplicate character')
  }
}

const deleteCharacter = async (character: Character) => {
  if (!confirm(`Are you sure you want to delete "${character.name}"? This action cannot be undone.`)) {
    return
  }

  try {
    // Note: You'll need to implement delete endpoint in the API
    // await charactersApi.delete(character.id)

    characters.value = characters.value.filter(c => c.id !== character.id)
    selectedCharacter.value = null
    toast.success('Character deleted successfully!')
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to delete character')
  }
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadCharacters()
})
</script>
