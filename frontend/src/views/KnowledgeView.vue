<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h2>知识管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建知识
      </el-button>
    </div>

    <!-- Search and Filter -->
    <el-card style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="选择分类" @change="loadKnowledge" clearable>
            <el-option label="座椅功能" value="seat_functions" />
            <el-option label="测试标准" value="test_standards" />
            <el-option label="失效模式" value="failure_modes" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.subcategory" placeholder="选择子分类" @change="loadKnowledge" clearable>
            <el-option label="记忆功能" value="memory" />
            <el-option label="加热功能" value="heating" />
            <el-option label="通风功能" value="ventilation" />
            <el-option label="按摩功能" value="massage" />
            <el-option label="安全功能" value="safety" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input 
            v-model="filters.search" 
            placeholder="搜索知识内容" 
            @input="loadKnowledge"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button @click="loadKnowledge" :loading="loading">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Knowledge List -->
    <el-card>
      <el-table :data="knowledge" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" size="small">
              {{ getCategoryText(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subcategory" label="子分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.subcategory" type="info" size="small">
              {{ row.subcategory }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.confidence * 100" 
              :color="getConfidenceColor(row.confidence)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewKnowledge(row.id)">查看</el-button>
            <el-button size="small" type="primary" @click="editKnowledge(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteKnowledge(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showCreateDialog" :title="editingKnowledge ? '编辑知识' : '新建知识'" width="800px">
      <el-form :model="knowledgeForm" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="knowledgeForm.title" placeholder="请输入知识标题" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="knowledgeForm.category" placeholder="选择分类">
            <el-option label="座椅功能" value="seat_functions" />
            <el-option label="测试标准" value="test_standards" />
            <el-option label="失效模式" value="failure_modes" />
          </el-select>
        </el-form-item>
        <el-form-item label="子分类">
          <el-select v-model="knowledgeForm.subcategory" placeholder="选择子分类" clearable>
            <el-option label="记忆功能" value="memory" />
            <el-option label="加热功能" value="heating" />
            <el-option label="通风功能" value="ventilation" />
            <el-option label="按摩功能" value="massage" />
            <el-option label="安全功能" value="safety" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="knowledgeForm.content" type="textarea" :rows="8" placeholder="请输入知识内容" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="knowledgeForm.tags" placeholder="请输入标签，用逗号分隔" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="knowledgeForm.source" placeholder="请输入知识来源" />
        </el-form-item>
        <el-form-item label="置信度">
          <el-slider v-model="knowledgeForm.confidence" :min="0" :max="1" :step="0.1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledge" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- View Dialog -->
    <el-dialog v-model="showViewDialog" title="知识详情" width="800px">
      <div v-if="viewingKnowledge">
        <h3>{{ viewingKnowledge.title }}</h3>
        <div class="knowledge-meta">
          <el-tag :type="getCategoryType(viewingKnowledge.category)" size="small">
            {{ getCategoryText(viewingKnowledge.category) }}
          </el-tag>
          <el-tag v-if="viewingKnowledge.subcategory" type="info" size="small">
            {{ viewingKnowledge.subcategory }}
          </el-tag>
          <span class="confidence">置信度: {{ (viewingKnowledge.confidence * 100).toFixed(1) }}%</span>
        </div>
        <div class="knowledge-content">
          {{ viewingKnowledge.content }}
        </div>
        <div class="knowledge-footer">
          <span>来源: {{ viewingKnowledge.source || '未知' }}</span>
          <span>使用次数: {{ viewingKnowledge.usage_count }}</span>
          <span>创建时间: {{ formatDate(viewingKnowledge.created_at) }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '@/api'

interface Knowledge {
  id: number
  title: string
  category: string
  subcategory?: string
  content: string
  tags?: string[]
  source?: string
  confidence: number
  usage_count: number
  created_at: string
}

const knowledge = ref<Knowledge[]>([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const editingKnowledge = ref<Knowledge | null>(null)
const viewingKnowledge = ref<Knowledge | null>(null)

const filters = ref({
  category: '',
  subcategory: '',
  search: ''
})

const knowledgeForm = ref({
  title: '',
  category: '',
  subcategory: '',
  content: '',
  tags: '',
  source: '',
  confidence: 0.8
})

onMounted(() => {
  loadKnowledge()
})

const loadKnowledge = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.category) {
      params.append('category', filters.value.category)
    }
    if (filters.value.subcategory) {
      params.append('subcategory', filters.value.subcategory)
    }
    if (filters.value.search) {
      params.append('search', filters.value.search)
    }

    const response = await api.get(`/api/v1/knowledge/?${params}`)
    knowledge.value = response
  } catch (error) {
    ElMessage.error('加载知识库失败')
  } finally {
    loading.value = false
  }
}

const saveKnowledge = async () => {
  if (!knowledgeForm.value.title || !knowledgeForm.value.category || !knowledgeForm.value.content) {
    ElMessage.warning('请填写必填字段')
    return
  }

  saving.value = true
  try {
    const formData = {
      ...knowledgeForm.value,
      tags: knowledgeForm.value.tags ? knowledgeForm.value.tags.split(',').map(t => t.trim()) : []
    }

    if (editingKnowledge.value) {
      await api.put(`/api/v1/knowledge/${editingKnowledge.value.id}`, formData)
      ElMessage.success('知识更新成功')
    } else {
      await api.post('/api/v1/knowledge/', formData)
      ElMessage.success('知识创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    loadKnowledge()
  } catch (error) {
    ElMessage.error(editingKnowledge.value ? '知识更新失败' : '知识创建失败')
  } finally {
    saving.value = false
  }
}

const editKnowledge = (item: Knowledge) => {
  editingKnowledge.value = item
  knowledgeForm.value = {
    title: item.title,
    category: item.category,
    subcategory: item.subcategory || '',
    content: item.content,
    tags: item.tags ? item.tags.join(', ') : '',
    source: item.source || '',
    confidence: item.confidence
  }
  showCreateDialog.value = true
}

const viewKnowledge = async (id: number) => {
  try {
    const response = await api.get(`/api/v1/knowledge/${id}`)
    viewingKnowledge.value = response
    showViewDialog.value = true
  } catch (error) {
    ElMessage.error('加载知识详情失败')
  }
}

const deleteKnowledge = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除此知识吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/api/v1/knowledge/${id}`)
    ElMessage.success('删除成功')
    loadKnowledge()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  editingKnowledge.value = null
  knowledgeForm.value = {
    title: '',
    category: '',
    subcategory: '',
    content: '',
    tags: '',
    source: '',
    confidence: 0.8
  }
}

const getCategoryType = (category: string) => {
  const types: Record<string, string> = {
    seat_functions: 'primary',
    test_standards: 'success',
    failure_modes: 'warning'
  }
  return types[category] || 'info'
}

const getCategoryText = (category: string) => {
  const texts: Record<string, string> = {
    seat_functions: '座椅功能',
    test_standards: '测试标准',
    failure_modes: '失效模式'
  }
  return texts[category] || category
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.knowledge-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.knowledge-meta {
  margin: 15px 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.confidence {
  color: #666;
  font-size: 14px;
}

.knowledge-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.knowledge-footer {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 14px;
  margin-top: 15px;
}
</style> 