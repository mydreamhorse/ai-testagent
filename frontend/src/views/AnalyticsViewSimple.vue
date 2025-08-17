<template>
  <div class="analytics-view-simple">
    <h1>数据分析页面测试</h1>
    <p>如果你能看到这个文字，说明Vue组件基本渲染正常</p>
    
    <div class="test-section">
      <h2>基础数据</h2>
      <div class="data-cards">
        <div class="card">
          <h3>{{ overviewData.requirements_count }}</h3>
          <p>需求总数</p>
        </div>
        <div class="card">
          <h3>{{ overviewData.test_cases_count }}</h3>
          <p>测试用例总数</p>
        </div>
        <div class="card">
          <h3>{{ overviewData.features_count }}</h3>
          <p>特征总数</p>
        </div>
        <div class="card">
          <h3>{{ overviewData.average_score.toFixed(1) }}</h3>
          <p>平均分数</p>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>API测试状态</h2>
      <div v-if="loading" class="loading">正在加载数据...</div>
      <div v-if="error" class="error">错误: {{ error }}</div>
      <div v-if="!loading && !error" class="success">数据加载成功</div>
    </div>

    <div class="test-section">
      <h2>操作测试</h2>
      <button @click="testAPI" :disabled="loading">测试API连接</button>
      <button @click="loadMockData">加载模拟数据</button>
    </div>

    <div class="test-section" v-if="apiResults.length > 0">
      <h2>API测试结果</h2>
      <ul>
        <li v-for="result in apiResults" :key="result.endpoint">
          <strong>{{ result.endpoint }}:</strong> 
          <span :class="result.success ? 'success' : 'error'">
            {{ result.success ? '成功' : '失败' }}
          </span>
          <span v-if="result.data"> - 数据: {{ JSON.stringify(result.data).substring(0, 100) }}...</span>
          <span v-if="result.error"> - 错误: {{ result.error }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface OverviewData {
  requirements_count: number
  test_cases_count: number
  features_count: number
  average_score: number
}

interface APIResult {
  endpoint: string
  success: boolean
  data?: any
  error?: string
}

const loading = ref(false)
const error = ref('')
const apiResults = ref<APIResult[]>([])

const overviewData = ref<OverviewData>({
  requirements_count: 0,
  test_cases_count: 0,
  features_count: 0,
  average_score: 0
})

const loadMockData = () => {
  overviewData.value = {
    requirements_count: 25,
    test_cases_count: 150,
    features_count: 75,
    average_score: 85.2
  }
  console.log('Mock data loaded:', overviewData.value)
}

const testAPI = async () => {
  loading.value = true
  error.value = ''
  apiResults.value = []
  
  try {
    // 测试健康检查
    const healthResult = await testEndpoint('GET', '/health')
    apiResults.value.push(healthResult)
    
    // 如果健康检查失败，不继续测试其他API
    if (!healthResult.success) {
      error.value = '后端服务不可用'
      return
    }
    
    // 测试其他API端点
    const endpoints = [
      '/api/v1/requirements/',
      '/api/v1/test-cases/',
    ]
    
    for (const endpoint of endpoints) {
      const result = await testEndpoint('GET', endpoint)
      apiResults.value.push(result)
    }
    
  } catch (err: any) {
    error.value = `API测试失败: ${err.message}`
    console.error('API test error:', err)
  } finally {
    loading.value = false
  }
}

const testEndpoint = async (method: string, endpoint: string): Promise<APIResult> => {
  try {
    const url = `http://localhost:8000${endpoint}`
    console.log(`Testing ${method} ${url}`)
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    if (!response.ok) {
      return {
        endpoint,
        success: false,
        error: `HTTP ${response.status}: ${response.statusText}`
      }
    }
    
    const data = await response.json()
    return {
      endpoint,
      success: true,
      data: Array.isArray(data) ? `Array(${data.length})` : data
    }
    
  } catch (err: any) {
    return {
      endpoint,
      success: false,
      error: err.message
    }
  }
}

onMounted(() => {
  console.log('AnalyticsViewSimple mounted')
  loadMockData()
  testAPI()
})
</script>

<style scoped>
.analytics-view-simple {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-top: 15px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #333;
}

.card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.loading {
  color: #409EFF;
  font-weight: bold;
}

.error {
  color: #F56C6C;
  font-weight: bold;
}

.success {
  color: #67C23A;
  font-weight: bold;
}

button {
  background: #409EFF;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

button:hover {
  background: #337ecc;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}
</style>