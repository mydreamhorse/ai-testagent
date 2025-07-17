<template>
  <div class="templates-view">
    <div class="page-header">
      <h2>模板管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建模板
      </el-button>
    </div>

    <!-- Search and Filter -->
    <el-card style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="选择分类" @change="loadTemplates" clearable>
            <el-option label="功能测试" value="function" />
            <el-option label="边界测试" value="boundary" />
            <el-option label="异常测试" value="exception" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input 
            v-model="filters.search" 
            placeholder="搜索模板名称" 
            @input="loadTemplates"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button @click="loadTemplates" :loading="loading">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Templates List -->
    <el-card>
      <el-table :data="templates" v-loading="loading">
        <el-table-column prop="name" label="模板名称" min-width="200" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" size="small">
              {{ getCategoryText(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="viewTemplate(row.id)">查看</el-button>
            <el-button size="small" type="primary" @click="editTemplate(row)">编辑</el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleTemplate(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteTemplate(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showCreateDialog" :title="editingTemplate ? '编辑模板' : '新建模板'" width="800px">
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="templateForm.category" placeholder="选择分类">
            <el-option label="功能测试" value="function" />
            <el-option label="边界测试" value="boundary" />
            <el-option label="异常测试" value="exception" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="templateForm.description" type="textarea" :rows="3" placeholder="请输入模板描述" />
        </el-form-item>
        <el-form-item label="模板内容" required>
          <el-input v-model="templateForm.template_content" type="textarea" :rows="12" placeholder="请输入模板内容" />
        </el-form-item>
        <el-form-item label="变量">
          <el-input v-model="templateForm.variables" type="textarea" :rows="3" placeholder="请输入变量定义（JSON格式）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- View Dialog -->
    <el-dialog v-model="showViewDialog" title="模板详情" width="800px">
      <div v-if="viewingTemplate">
        <h3>{{ viewingTemplate.name }}</h3>
        <div class="template-meta">
          <el-tag :type="getCategoryType(viewingTemplate.category)" size="small">
            {{ getCategoryText(viewingTemplate.category) }}
          </el-tag>
          <span class="usage-count">使用次数: {{ viewingTemplate.usage_count }}</span>
          <span class="status">状态: {{ viewingTemplate.is_active ? '启用' : '禁用' }}</span>
        </div>
        <div class="template-description">
          {{ viewingTemplate.description }}
        </div>
        <div class="template-content">
          <h4>模板内容:</h4>
          <pre>{{ viewingTemplate.template_content }}</pre>
        </div>
        <div v-if="viewingTemplate.variables" class="template-variables">
          <h4>变量定义:</h4>
          <pre>{{ JSON.stringify(viewingTemplate.variables, null, 2) }}</pre>
        </div>
        <div class="template-footer">
          <span>创建时间: {{ formatDate(viewingTemplate.created_at) }}</span>
          <span>更新时间: {{ formatDate(viewingTemplate.updated_at) }}</span>
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

interface Template {
  id: number
  name: string
  category: string
  description?: string
  template_content: string
  variables?: any
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

const templates = ref<Template[]>([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const editingTemplate = ref<Template | null>(null)
const viewingTemplate = ref<Template | null>(null)

const filters = ref({
  category: '',
  search: ''
})

const templateForm = ref({
  name: '',
  category: '',
  description: '',
  template_content: '',
  variables: ''
})

onMounted(() => {
  loadTemplates()
})

const loadTemplates = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.category) {
      params.append('category', filters.value.category)
    }
    if (filters.value.search) {
      params.append('search', filters.value.search)
    }

    const response = await api.get(`/api/v1/templates/?${params}`)
    templates.value = response
  } catch (error) {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const saveTemplate = async () => {
  if (!templateForm.value.name || !templateForm.value.category || !templateForm.value.template_content) {
    ElMessage.warning('请填写必填字段')
    return
  }

  saving.value = true
  try {
    const formData = {
      ...templateForm.value,
      variables: templateForm.value.variables ? JSON.parse(templateForm.value.variables) : {}
    }

    if (editingTemplate.value) {
      await api.put(`/api/v1/templates/${editingTemplate.value.id}`, formData)
      ElMessage.success('模板更新成功')
    } else {
      await api.post('/api/v1/templates/', formData)
      ElMessage.success('模板创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    loadTemplates()
  } catch (error) {
    ElMessage.error(editingTemplate.value ? '模板更新失败' : '模板创建失败')
  } finally {
    saving.value = false
  }
}

const editTemplate = (item: Template) => {
  editingTemplate.value = item
  templateForm.value = {
    name: item.name,
    category: item.category,
    description: item.description || '',
    template_content: item.template_content,
    variables: item.variables ? JSON.stringify(item.variables, null, 2) : ''
  }
  showCreateDialog.value = true
}

const viewTemplate = async (id: number) => {
  try {
    const response = await api.get(`/api/v1/templates/${id}`)
    viewingTemplate.value = response
    showViewDialog.value = true
  } catch (error) {
    ElMessage.error('加载模板详情失败')
  }
}

const toggleTemplate = async (template: Template) => {
  try {
    const action = template.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(`确定${action}此模板吗？`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.put(`/api/v1/templates/${template.id}`, {
      ...template,
      is_active: !template.is_active
    })
    ElMessage.success(`${action}成功`)
    loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const deleteTemplate = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除此模板吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/api/v1/templates/${id}`)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  editingTemplate.value = null
  templateForm.value = {
    name: '',
    category: '',
    description: '',
    template_content: '',
    variables: ''
  }
}

const getCategoryType = (category: string) => {
  const types: Record<string, string> = {
    function: 'primary',
    boundary: 'warning',
    exception: 'danger',
    performance: 'info',
    security: 'success'
  }
  return types[category] || 'info'
}

const getCategoryText = (category: string) => {
  const texts: Record<string, string> = {
    function: '功能测试',
    boundary: '边界测试',
    exception: '异常测试',
    performance: '性能测试',
    security: '安全测试'
  }
  return texts[category] || category
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.templates-view {
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

.template-meta {
  margin: 15px 0;
  display: flex;
  gap: 15px;
  align-items: center;
}

.usage-count, .status {
  color: #666;
  font-size: 14px;
}

.template-description {
  margin: 15px 0;
  color: #666;
  line-height: 1.6;
}

.template-content, .template-variables {
  margin: 15px 0;
}

.template-content h4, .template-variables h4 {
  margin-bottom: 10px;
  color: #333;
}

.template-content pre, .template-variables pre {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.4;
}

.template-footer {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 14px;
  margin-top: 15px;
}
</style> 