<template>
  <AppLayout>
    <div class="space-y-6">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Settings</h1>
        <p class="text-muted-foreground">
          Configure your CharForge environment and API keys
        </p>
      </div>

      <!-- Environment Settings -->
      <Card class="p-6">
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold">Environment Configuration</h3>
              <p class="text-sm text-muted-foreground">
                Configure API keys and paths for CharForge integration
              </p>
            </div>
            <Button @click="testEnvironment" :disabled="isTestingEnv" variant="outline">
              <TestTube class="mr-2 h-4 w-4" />
              {{ isTestingEnv ? 'Testing...' : 'Test Configuration' }}
            </Button>
          </div>

          <form @submit.prevent="saveEnvironmentSettings" class="space-y-4">
            <div class="grid gap-4 md:grid-cols-2">
              <!-- HuggingFace Token -->
              <div class="space-y-2">
                <label class="text-sm font-medium">HuggingFace Token</label>
                <Input
                  v-model="envSettings.HF_TOKEN"
                  type="password"
                  placeholder="hf_..."
                  class="font-mono"
                />
                <p class="text-xs text-muted-foreground">
                  Required for downloading models from HuggingFace
                </p>
                <div v-if="testResults.HF_TOKEN" class="flex items-center text-xs">
                  <CheckCircle v-if="testResults.HF_TOKEN.valid" class="mr-1 h-3 w-3 text-green-500" />
                  <XCircle v-else class="mr-1 h-3 w-3 text-red-500" />
                  {{ testResults.HF_TOKEN.message }}
                </div>
              </div>

              <!-- HuggingFace Home -->
              <div class="space-y-2">
                <label class="text-sm font-medium">HuggingFace Cache Directory</label>
                <Input
                  v-model="envSettings.HF_HOME"
                  type="text"
                  placeholder="/path/to/huggingface/cache"
                  class="font-mono"
                />
                <p class="text-xs text-muted-foreground">
                  Directory to cache downloaded models
                </p>
                <div v-if="testResults.HF_HOME" class="flex items-center text-xs">
                  <CheckCircle v-if="testResults.HF_HOME.valid" class="mr-1 h-3 w-3 text-green-500" />
                  <XCircle v-else class="mr-1 h-3 w-3 text-red-500" />
                  {{ testResults.HF_HOME.message }}
                </div>
              </div>

              <!-- Google API Key -->
              <div class="space-y-2">
                <label class="text-sm font-medium">Google GenAI API Key</label>
                <Input
                  v-model="envSettings.GOOGLE_API_KEY"
                  type="password"
                  placeholder="AIza..."
                  class="font-mono"
                />
                <p class="text-xs text-muted-foreground">
                  Required for image captioning and prompt optimization
                </p>
                <div v-if="testResults.GOOGLE_API_KEY" class="flex items-center text-xs">
                  <CheckCircle v-if="testResults.GOOGLE_API_KEY.valid" class="mr-1 h-3 w-3 text-green-500" />
                  <XCircle v-else class="mr-1 h-3 w-3 text-red-500" />
                  {{ testResults.GOOGLE_API_KEY.message }}
                </div>
              </div>

              <!-- FAL Key -->
              <div class="space-y-2">
                <label class="text-sm font-medium">FAL.AI API Key</label>
                <Input
                  v-model="envSettings.FAL_KEY"
                  type="password"
                  placeholder="fal_..."
                  class="font-mono"
                />
                <p class="text-xs text-muted-foreground">
                  Required for upscaling and PuLID-Flux image generation
                </p>
                <div v-if="testResults.FAL_KEY" class="flex items-center text-xs">
                  <CheckCircle v-if="testResults.FAL_KEY.valid" class="mr-1 h-3 w-3 text-green-500" />
                  <XCircle v-else class="mr-1 h-3 w-3 text-red-500" />
                  {{ testResults.FAL_KEY.message }}
                </div>
              </div>

              <!-- CivitAI Key -->
              <div class="space-y-2">
                <label class="text-sm font-medium">CivitAI API Key</label>
                <Input
                  v-model="envSettings.CIVITAI_API_KEY"
                  type="password"
                  placeholder="civitai_..."
                  class="font-mono"
                />
                <p class="text-xs text-muted-foreground">
                  Optional: For accessing CivitAI models
                </p>
                <div v-if="testResults.CIVITAI_API_KEY" class="flex items-center text-xs">
                  <CheckCircle v-if="testResults.CIVITAI_API_KEY.valid" class="mr-1 h-3 w-3 text-green-500" />
                  <XCircle v-else class="mr-1 h-3 w-3 text-red-500" />
                  {{ testResults.CIVITAI_API_KEY.message }}
                </div>
              </div>
            </div>

            <div class="flex justify-end space-x-3">
              <Button type="button" variant="outline" @click="loadEnvironmentSettings">
                Reset
              </Button>
              <Button type="submit" :disabled="isSaving">
                <Save class="mr-2 h-4 w-4" />
                {{ isSaving ? 'Saving...' : 'Save Configuration' }}
              </Button>
            </div>
          </form>
        </div>
      </Card>

      <!-- System Information -->
      <Card class="p-6">
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">System Information</h3>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-2">
              <label class="text-sm font-medium">Backend Status</label>
              <div class="flex items-center space-x-2">
                <div class="h-2 w-2 bg-green-500 rounded-full"></div>
                <span class="text-sm">Connected</span>
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium">API Version</label>
              <span class="text-sm text-muted-foreground">v1.0.0</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import { CheckCircle, XCircle, TestTube, Save } from 'lucide-vue-next'
import AppLayout from '@/components/layout/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { settingsApi } from '@/services/api'

const toast = useToast()

const envSettings = ref({
  HF_TOKEN: '',
  HF_HOME: '',
  CIVITAI_API_KEY: '',
  GOOGLE_API_KEY: '',
  FAL_KEY: ''
})

const testResults = ref<Record<string, { valid: boolean; message: string }>>({})
const isSaving = ref(false)
const isTestingEnv = ref(false)

const loadEnvironmentSettings = async () => {
  try {
    const settings = await settingsApi.getEnvironment()
    envSettings.value = settings
  } catch (error) {
    toast.error('Failed to load environment settings')
  }
}

const saveEnvironmentSettings = async () => {
  isSaving.value = true
  try {
    await settingsApi.saveEnvironment(envSettings.value)
    toast.success('Environment settings saved successfully!')
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to save settings')
  } finally {
    isSaving.value = false
  }
}

const testEnvironment = async () => {
  isTestingEnv.value = true
  try {
    const results = await settingsApi.testEnvironment()
    testResults.value = results

    const validCount = Object.values(results).filter(r => r.valid).length
    const totalCount = Object.keys(results).length

    if (validCount === totalCount) {
      toast.success('All environment settings are valid!')
    } else {
      toast.warning(`${validCount}/${totalCount} settings are valid`)
    }
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Failed to test environment')
  } finally {
    isTestingEnv.value = false
  }
}

onMounted(() => {
  loadEnvironmentSettings()
})
</script>
