<template>
  <Card class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold">Advanced Training Options</h3>
      <Button
        @click="showAdvanced = !showAdvanced"
        variant="outline"
        size="sm"
      >
        {{ showAdvanced ? 'Hide' : 'Show' }} Advanced
      </Button>
    </div>
    
    <div v-if="showAdvanced" class="space-y-6">
      <!-- Optimizer Configuration -->
      <div class="grid md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-2">Optimizer</label>
          <select
            v-model="config.optimizer"
            class="w-full px-3 py-2 border border-input rounded-md"
          >
            <option
              v-for="optimizer in availableOptimizers"
              :key="optimizer.value"
              :value="optimizer.value"
            >
              {{ optimizer.name }}
            </option>
          </select>
          <p class="text-xs text-muted-foreground mt-1">
            AdamW is recommended for most cases
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">Weight Decay</label>
          <Input
            v-model.number="config.weightDecay"
            type="number"
            step="0.001"
            min="0"
            max="0.1"
            class="w-full"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Regularization strength (0.01 recommended)
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">Learning Rate Scheduler</label>
          <select
            v-model="config.lrScheduler"
            class="w-full px-3 py-2 border border-input rounded-md"
          >
            <option value="constant">Constant</option>
            <option value="cosine">Cosine</option>
            <option value="linear">Linear</option>
            <option value="polynomial">Polynomial</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">Gradient Accumulation</label>
          <Input
            v-model.number="config.gradientAccumulation"
            type="number"
            min="1"
            max="16"
            class="w-full"
          />
          <p class="text-xs text-muted-foreground mt-1">
            Effective batch size = batch_size × accumulation
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">Mixed Precision</label>
          <select
            v-model="config.mixedPrecision"
            class="w-full px-3 py-2 border border-input rounded-md"
          >
            <option value="fp16">FP16 (Recommended)</option>
            <option value="bf16">BF16</option>
            <option value="fp32">FP32</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium mb-2">Save Every (Steps)</label>
          <Input
            v-model.number="config.saveEvery"
            type="number"
            min="50"
            max="1000"
            step="50"
            class="w-full"
          />
        </div>
      </div>
      
      <!-- Training Options -->
      <div class="space-y-3">
        <h4 class="font-medium">Training Options</h4>
        <div class="grid md:grid-cols-2 gap-4">
          <label class="flex items-center space-x-2">
            <input
              v-model="config.gradientCheckpointing"
              type="checkbox"
              class="rounded border-input"
            />
            <span class="text-sm">Gradient Checkpointing</span>
            <span class="text-xs text-muted-foreground">(Saves VRAM)</span>
          </label>
          
          <label class="flex items-center space-x-2">
            <input
              v-model="config.trainTextEncoder"
              type="checkbox"
              class="rounded border-input"
            />
            <span class="text-sm">Train Text Encoder</span>
            <span class="text-xs text-muted-foreground">(More control)</span>
          </label>
        </div>
      </div>
      
      <!-- Trainer Selection -->
      <div>
        <h4 class="font-medium mb-3">Training Method</h4>
        <div class="grid md:grid-cols-2 gap-4">
          <div
            v-for="trainer in availableTrainers"
            :key="trainer.name"
            class="border rounded-lg p-4 cursor-pointer transition-colors"
            :class="{
              'border-primary bg-primary/5': selectedTrainer === trainer.type,
              'border-input hover:border-primary/50': selectedTrainer !== trainer.type
            }"
            @click="selectedTrainer = trainer.type"
          >
            <div class="flex items-center space-x-2 mb-2">
              <input
                :checked="selectedTrainer === trainer.type"
                type="radio"
                class="text-primary"
                readonly
              />
              <h5 class="font-medium">{{ trainer.name }}</h5>
            </div>
            <p class="text-sm text-muted-foreground">{{ trainer.description }}</p>
          </div>
        </div>
      </div>
      
      <!-- ComfyUI Model Selection -->
      <div>
        <h4 class="font-medium mb-3">ComfyUI Model Override</h4>
        <p class="text-sm text-muted-foreground mb-4">
          Select specific ComfyUI models to use instead of defaults. Models will be copied with standard names to maintain compatibility.
        </p>
        
        <div class="grid md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-2">Checkpoint</label>
            <select
              v-model="config.comfyuiCheckpoint"
              class="w-full px-3 py-2 border border-input rounded-md"
            >
              <option value="">Use Default</option>
              <option
                v-for="model in availableModels.checkpoints"
                :key="model.path"
                :value="model.path"
              >
                {{ model.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-2">VAE</label>
            <select
              v-model="config.comfyuiVae"
              class="w-full px-3 py-2 border border-input rounded-md"
            >
              <option value="">Use Default</option>
              <option
                v-for="vae in availableModels.vaes"
                :key="vae.path"
                :value="vae.path"
              >
                {{ vae.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-2">LoRA (Optional)</label>
            <select
              v-model="config.comfyuiLora"
              class="w-full px-3 py-2 border border-input rounded-md"
            >
              <option value="">None</option>
              <option
                v-for="lora in availableModels.loras"
                :key="lora.path"
                :value="lora.path"
              >
                {{ lora.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'

interface Props {
  config: any
  availableOptimizers: any[]
  availableTrainers: any[]
  availableModels: any
}

interface Emits {
  (e: 'update:config', value: any): void
  (e: 'update:selectedTrainer', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const showAdvanced = ref(false)
const selectedTrainer = ref('lora')

// Watch for trainer changes
const selectTrainer = (trainerType: string) => {
  selectedTrainer.value = trainerType
  emit('update:selectedTrainer', trainerType)
}
</script>
