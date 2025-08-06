<template>
  <div class="flex h-screen bg-background">
    <!-- Sidebar -->
    <aside class="w-64 bg-card border-r border-border">
      <div class="p-6">
        <h1 class="text-xl font-bold">CharForge</h1>
        <p class="text-sm text-muted-foreground">AI Character LoRA</p>
      </div>
      
      <nav class="px-4 space-y-2">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.href"
          :data-tour="item.tourId"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
          :class="[
            $route.path === item.href
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
          ]"
        >
          <component :is="item.icon" class="mr-3 h-4 w-4" />
          {{ item.name }}
        </router-link>
      </nav>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="bg-card border-b border-border px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h2 class="text-lg font-semibold">{{ pageTitle }}</h2>
          </div>
          
          <div class="flex items-center space-x-4">
            <!-- User menu (only show when auth is enabled) -->
            <div v-if="authStore.authEnabled" class="relative">
              <Button @click="showUserMenu = !showUserMenu" variant="ghost" size="sm">
                <User class="h-4 w-4 mr-2" />
                {{ authStore.user?.username }}
              </Button>

              <div
                v-if="showUserMenu"
                class="absolute right-0 mt-2 w-48 bg-popover border border-border rounded-md shadow-lg z-50"
              >
                <div class="py-1">
                  <router-link
                    to="/settings"
                    class="block px-4 py-2 text-sm hover:bg-accent"
                    @click="showUserMenu = false"
                  >
                    Settings
                  </router-link>
                  <button
                    @click="authStore.logout()"
                    class="block w-full text-left px-4 py-2 text-sm hover:bg-accent"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>

            <!-- Show simple user indicator when auth is disabled -->
            <div v-else class="flex items-center text-sm text-muted-foreground">
              <User class="h-4 w-4 mr-2" />
              CharForge User
            </div>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  Users,
  Database,
  Zap,
  Wand2,
  Image,
  Upload,
  Settings,
  User
} from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const authStore = useAuthStore()
const showUserMenu = ref(false)

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, tourId: 'dashboard-link' },
  { name: 'Characters', href: '/characters', icon: Users, tourId: 'characters-link' },
  { name: 'Datasets', href: '/datasets', icon: Database, tourId: 'datasets-link' },
  { name: 'Training', href: '/training', icon: Zap, tourId: 'training-link' },
  { name: 'Inference', href: '/inference', icon: Wand2, tourId: 'inference-link' },
  { name: 'Gallery', href: '/gallery', icon: Image, tourId: 'gallery-link' },
  { name: 'Media', href: '/media', icon: Upload, tourId: 'media-link' },
  { name: 'Settings', href: '/settings', icon: Settings, tourId: 'settings-link' },
]

const pageTitle = computed(() => {
  const currentNav = navigation.find(item => item.href === route.path)
  return currentNav?.name || 'CharForge'
})
</script>
