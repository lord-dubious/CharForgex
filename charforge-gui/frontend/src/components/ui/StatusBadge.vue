<template>
  <span
    :class="cn(
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
      statusVariants[status] || statusVariants.default
    )"
  >
    <div
      :class="cn(
        'mr-1.5 h-2 w-2 rounded-full',
        dotVariants[status] || dotVariants.default
      )"
    />
    {{ statusLabels[status] || status }}
  </span>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  status: string
}

defineProps<Props>()

const statusVariants = {
  created: 'bg-gray-100 text-gray-800',
  training: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  default: 'bg-gray-100 text-gray-800'
}

const dotVariants = {
  created: 'bg-gray-400',
  training: 'bg-blue-400 animate-pulse',
  completed: 'bg-green-400',
  failed: 'bg-red-400',
  pending: 'bg-yellow-400',
  running: 'bg-blue-400 animate-pulse',
  default: 'bg-gray-400'
}

const statusLabels = {
  created: 'Created',
  training: 'Training',
  completed: 'Completed',
  failed: 'Failed',
  pending: 'Pending',
  running: 'Running'
}
</script>
