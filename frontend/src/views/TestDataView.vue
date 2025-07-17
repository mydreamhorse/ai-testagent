<template>
  <div class="test-data-view">
    <h2>数据测试页面</h2>
    
    <el-card>
      <template #header>
        <span>认证状态</span>
      </template>
      <p>Token: {{ userStore.token ? '已设置' : '未设置' }}</p>
      <p>认证状态: {{ userStore.isAuthenticated ? '已认证' : '未认证' }}</p>
      <p>用户信息: {{ userStore.user ? userStore.user.username : '未加载' }}</p>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>需求数据</span>
      </template>
      <el-button @click="loadRequirements" :loading="loading">加载需求数据</el-button>
      <div v-if="requirements.length > 0">
        <p>共 {{ requirements.length }} 条需求</p>
        <ul>
          <li v-for="req in requirements.slice(0, 3)" :key="req.id">
            {{ req.title }}
          </li>
        </ul>
      </div>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>测试用例数据</span>
      </template>
      <el-button @click="loadTestCases" :loading="loading">加载测试用例数据</el-button>
      <div v-if="testCases.length > 0">
        <p>共 {{ testCases.length }} 条测试用例</p>
        <ul>
          <li v-for="tc in testCases.slice(0, 3)" :key="tc.id">
            {{ tc.title }}
          </li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const userStore = useUserStore()
const loading = ref(false)
const requirements = ref([])
const testCases = ref([])

const loadRequirements = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/requirements/')
    requirements.value = response
    console.log('需求数据:', response)
  } catch (error) {
    console.error('加载需求失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTestCases = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/test-cases/')
    testCases.value = response
    console.log('测试用例数据:', response)
  } catch (error) {
    console.error('加载测试用例失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.test-data-view {
  padding: 20px;
}
</style> 