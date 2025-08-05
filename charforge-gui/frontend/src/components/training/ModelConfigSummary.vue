<template>
  <Card class="p-6">
    <h3 class="text-lg font-semibold mb-4">Training Configuration Summary</h3>
    
    <div class="space-y-4">
      <!-- Model Configuration -->
      <div>
        <h4 class="font-medium text-sm text-muted-foreground mb-2">MODEL CONFIGURATION</h4>
        <div class="grid md:grid-cols-2 gap-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Base Model:</span>
            <span class="font-medium">{{ getModelName(config.modelConfig.baseModel) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">VAE:</span>
            <span class="font-medium">{{ getModelName(config.modelConfig.vaeModel) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Scheduler:</span>
            <span class="font-medium">{{ config.modelConfig.scheduler.toUpperCase() }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Data Type:</span>
            <span class="font-medium">{{ config.modelConfig.dtype }}</span>
          </div>
        </div>
      </div>
      
      <!-- Training Parameters -->
      <div>
        <h4 class="font-medium text-sm text-muted-foreground mb-2">TRAINING PARAMETERS</h4>
        <div class="grid md:grid-cols-3 gap-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Steps:</span>
            <span class="font-medium">{{ config.steps }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Learning Rate:</span>
            <span class="font-medium">{{ config.learning_rate }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Batch Size:</span>
            <span class="font-medium">{{ config.batch_size }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Train Dim:</span>
            <span class="font-medium">{{ config.train_dim }}x{{ config.train_dim }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">LoRA Rank:</span>
            <span class="font-medium">{{ config.rank_dim }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">PuLID Images:</span>
            <span class="font-medium">{{ config.pulidflux_images }}</span>
          </div>
        </div>
      </div>
      
      <!-- MV Adapter Configuration -->
      <div v-if="config.mvAdapterConfig.enabled">
        <h4 class="font-medium text-sm text-muted-foreground mb-2">MV ADAPTER</h4>
        <div class="grid md:grid-cols-3 gap-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Views:</span>
            <span class="font-medium">{{ config.mvAdapterConfig.numViews }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Resolution:</span>
            <span class="font-medium">{{ config.mvAdapterConfig.width }}x{{ config.mvAdapterConfig.height }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Guidance:</span>
            <span class="font-medium">{{ config.mvAdapterConfig.guidanceScale }}</span>
          </div>
        </div>
      </div>
      
      <!-- Advanced Configuration -->
      <div>
        <h4 class="font-medium text-sm text-muted-foreground mb-2">ADVANCED OPTIONS</h4>
        <div class="grid md:grid-cols-3 gap-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Optimizer:</span>
            <span class="font-medium">{{ config.advancedConfig.optimizer.toUpperCase() }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Weight Decay:</span>
            <span class="font-medium">{{ config.advancedConfig.weightDecay }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Mixed Precision:</span>
            <span class="font-medium">{{ config.advancedConfig.mixedPrecision.toUpperCase() }}</span>
          </div>
        </div>
        
        <div class="flex flex-wrap gap-2 mt-3">
          <span
            v-if="config.advancedConfig.gradientCheckpointing"
            class="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
          >
            Gradient Checkpointing
          </span>
          <span
            v-if="config.advancedConfig.trainTextEncoder"
            class="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
          >
            Train Text Encoder
          </span>
          <span
            v-if="config.mvAdapterConfig.enabled"
            class="px-2 py-1 bg-secondary/10 text-secondary text-xs rounded-full"
          >
            MV Adapter Enabled
          </span>
        </div>
      </div>
      
      <!-- ComfyUI Overrides -->
      <div v-if="hasComfyUIOverrides">
        <h4 class="font-medium text-sm text-muted-foreground mb-2">COMFYUI OVERRIDES</h4>
        <div class="space-y-2 text-sm">
          <div v-if="config.comfyuiCheckpoint" class="flex justify-between">
            <span class="text-muted-foreground">Checkpoint:</span>
            <span class="font-medium">{{ getModelName(config.comfyuiCheckpoint) }}</span>
          </div>
          <div v-if="config.comfyuiVae" class="flex justify-between">
            <span class="text-muted-foreground">VAE:</span>
            <span class="font-medium">{{ getModelName(config.comfyuiVae) }}</span>
          </div>
          <div v-if="config.comfyuiLora" class="flex justify-between">
            <span class="text-muted-foreground">LoRA:</span>
            <span class="font-medium">{{ getModelName(config.comfyuiLora) }}</span>
          </div>
        </div>
      </div>
      
      <!-- Estimated Training Time -->
      <div class="border-t pt-4">
        <div class="flex justify-between items-center">
          <span class="text-sm text-muted-foreground">Estimated Training Time:</span>
          <span class="font-medium text-lg">{{ estimatedTime }}</span>
        </div>
        <p class="text-xs text-muted-foreground mt-1">
          Based on {{ config.steps }} steps with current configuration
        </p>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue'
import Card from '@/components/ui/Card.vue'

interface Props {
  config: any
}

const props = defineProps<Props>()

const hasComfyUIOverrides = computed(() => {
  return props.config.comfyuiCheckpoint || props.config.comfyuiVae || props.config.comfyuiLora
})

const estimatedTime = computed(() => {
  // Rough estimation based on steps and configuration
  const baseTimePerStep = 2 // seconds per step
  let multiplier = 1
  
  // Adjust for resolution
  if (props.config.train_dim >= 1024) multiplier *= 1.5
  if (props.config.train_dim >= 768) multiplier *= 1.2
  
  // Adjust for batch size
  multiplier *= props.config.batch_size
  
  // Adjust for MV Adapter
  if (props.config.mvAdapterConfig.enabled) {
    multiplier *= 1.8
  }
  
  // Adjust for advanced options
  if (props.config.advancedConfig.trainTextEncoder) multiplier *= 1.3
  if (!props.config.advancedConfig.gradientCheckpointing) multiplier *= 1.2
  
  const totalSeconds = props.config.steps * baseTimePerStep * multiplier
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  } else {
    return `${minutes}m`
  }
})

const getModelName = (path: string): string => {
  if (!path) return 'Default'
  
  // Extract model name from path
  if (path.includes('/')) {
    const parts = path.split('/')
    return parts[parts.length - 1].replace(/\.(safetensors|ckpt|pt)$/, '')
  }
  
  return path
}
</script>
