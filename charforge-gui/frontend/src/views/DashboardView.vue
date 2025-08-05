<template>
  <div class="min-h-screen bg-background">
    <AppLayout>
      <div class="space-y-6">
        <!-- Header -->
        <div>
          <h1 class="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p class="text-muted-foreground">
            Welcome to CharForge - AI-Powered Character LoRA Creation
          </p>
        </div>

        <!-- Quick Stats -->
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card class="p-6">
            <div class="flex items-center space-x-2">
              <div class="text-2xl font-bold">{{ stats.characters }}</div>
              <div class="text-sm text-muted-foreground">Characters</div>
            </div>
          </Card>
          
          <Card class="p-6">
            <div class="flex items-center space-x-2">
              <div class="text-2xl font-bold">{{ stats.trainingSessions }}</div>
              <div class="text-sm text-muted-foreground">Training Sessions</div>
            </div>
          </Card>
          
          <Card class="p-6">
            <div class="flex items-center space-x-2">
              <div class="text-2xl font-bold">{{ stats.inferenceJobs }}</div>
              <div class="text-sm text-muted-foreground">Generated Images</div>
            </div>
          </Card>
          
          <Card class="p-6">
            <div class="flex items-center space-x-2">
              <div class="text-2xl font-bold">{{ stats.mediaFiles }}</div>
              <div class="text-sm text-muted-foreground">Media Files</div>
            </div>
          </Card>
        </div>

        <!-- Quick Actions -->
        <div class="grid gap-6 md:grid-cols-2">
          <Card class="p-6">
            <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
            <div class="space-y-3">
              <Button @click="$router.push('/characters/create')" class="w-full justify-start">
                <Plus class="mr-2 h-4 w-4" />
                Create New Character
              </Button>
              <Button @click="$router.push('/media')" variant="outline" class="w-full justify-start">
                <Upload class="mr-2 h-4 w-4" />
                Upload Media
              </Button>
              <Button @click="$router.push('/inference')" variant="outline" class="w-full justify-start">
                <Wand2 class="mr-2 h-4 w-4" />
                Generate Images
              </Button>
            </div>
          </Card>

          <Card class="p-6">
            <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
            <div class="space-y-3">
              <div v-if="recentActivity.length === 0" class="text-sm text-muted-foreground">
                No recent activity
              </div>
              <div v-else v-for="activity in recentActivity" :key="activity.id" class="text-sm">
                <div class="font-medium">{{ activity.title }}</div>
                <div class="text-muted-foreground">{{ activity.description }}</div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Upload, Wand2 } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const stats = ref({
  characters: 0,
  trainingSessions: 0,
  inferenceJobs: 0,
  mediaFiles: 0
})

const recentActivity = ref([])

onMounted(async () => {
  // Load dashboard data
  // This would typically fetch from API
})
</script>
