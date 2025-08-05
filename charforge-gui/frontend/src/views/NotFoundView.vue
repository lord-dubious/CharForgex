<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-foreground mb-4">404</h1>
      <p class="text-muted-foreground mb-6">Page not found</p>
      <Button @click="$router.push('/')">Go Home</Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
</script>
