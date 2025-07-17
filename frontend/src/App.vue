<template>
  <div id="app">
    <el-container>
      <el-header v-if="!isLoginPage">
        <AppHeader />
      </el-header>
      <el-container>
        <el-aside v-if="!isLoginPage && userStore.isAuthenticated" width="250px">
          <AppSidebar />
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()
const userStore = useUserStore()

const isLoginPage = computed(() => route.path === '/login')

// Force logout if no token exists
if (!userStore.isAuthenticated) {
  userStore.logout()
}
</script>

<style scoped>
#app {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-header {
  background-color: #409eff;
  color: white;
  padding: 0;
}

.el-aside {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e8eb;
}

.el-main {
  padding: 20px;
  background-color: #f0f2f5;
}
</style>