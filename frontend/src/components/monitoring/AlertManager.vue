<template>
  <div class="alert-manager">
    <el-card>
      <template #header>
        <div class="alert-header">
          <span>告警管理</span>
          <div class="header-actions">
            <el-button size="small" @click="createAlertRule">
              <el-icon><Plus /></el-icon>
              新建规则
            </el-button>
            <el-button size="small" @click="refreshAlerts">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 告警规则管理 -->
      <div class="alert-rules-section">
        <h3>告警规则</h3>
        <el-table :data="alertRules" size="small">
          <el-table-column prop="name" label="规则名称" />
          <el-table-column prop="metric" label="监控指标" />
          <el-table-column prop="condition" label="触发条件" />
          <el-table-column prop="threshold" label="阈值" />
          <el-table-column prop="severity" label="严重程度">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" size="small">
                {{ getSeverityText(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-switch 
                v-model="row.enabled" 
                @change="toggleRule(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="text" @click="editRule(row)">
                编辑
              </el-button>
              <el-button size="small" type="text" @click="testRule(row)">
                测试
              </el-button>
              <el-button 
                size="small" 
                type="text" 
                style="color: #f56c6c;"
                @click="deleteRule(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 告警历史 -->
      <div class="alert-history-section">
        <h3>告警历史</h3>
        <div class="history-filters">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            @change="filterAlerts"
          />
          <el-select v-model="severityFilter" size="small" placeholder="严重程度">
            <el-option label="全部" value="" />
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
          <el-select v-model="statusFilter" size="small" placeholder="状态">
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已忽略" value="ignored" />
          </el-select>
        </div>

        <el-table 
          :data="filteredAlertHistory" 
          size="small" 
          max-height="400"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="severity" label="级别" width="80">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" size="small">
                {{ getSeverityText(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="告警内容" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="120" />
          <el-table-column prop="triggered_at" label="触发时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.triggered_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="resolved_at" label="解决时间" width="160">
            <template #default="{ row }">
              {{ row.resolved_at ? formatTime(row.resolved_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag 
                :type="getStatusType(row.status)" 
                size="small"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button 
                v-if="row.status === 'active'"
                size="small" 
                type="text" 
                @click="resolveAlert(row)"
              >
                解决
              </el-button>
              <el-button 
                v-if="row.status === 'active'"
                size="small" 
                type="text" 
                @click="ignoreAlert(row)"
              >
                忽略
              </el-button>
              <el-button 
                size="small" 
                type="text" 
                @click="viewAlertDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 批量操作 -->
        <div class="batch-actions" v-if="selectedAlerts.length > 0">
          <span>已选择 {{ selectedAlerts.length }} 项</span>
          <el-button size="small" @click="batchResolve">批量解决</el-button>
          <el-button size="small" @click="batchIgnore">批量忽略</el-button>
          <el-button size="small" @click="batchDelete">批量删除</el-button>
        </div>
      </div>
    </el-card>

    <!-- 告警规则编辑对话框 -->
    <el-dialog
      v-model="ruleDialogVisible"
      :title="editingRule.id ? '编辑告警规则' : '新建告警规则'"
      width="600px"
    >
      <el-form :model="editingRule" :rules="ruleFormRules" ref="ruleForm" label-width="100px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="editingRule.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="监控指标" prop="metric">
          <el-select v-model="editingRule.metric" placeholder="选择监控指标">
            <el-option label="CPU使用率" value="cpu_usage" />
            <el-option label="内存使用率" value="memory_usage" />
            <el-option label="磁盘使用率" value="disk_usage" />
            <el-option label="错误率" value="error_rate" />
            <el-option label="响应时间" value="response_time" />
            <el-option label="测试失败率" value="test_failure_rate" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发条件" prop="condition">
          <el-select v-model="editingRule.condition" placeholder="选择条件">
            <el-option label="大于" value="gt" />
            <el-option label="大于等于" value="gte" />
            <el-option label="小于" value="lt" />
            <el-option label="小于等于" value="lte" />
            <el-option label="等于" value="eq" />
            <el-option label="不等于" value="ne" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值" prop="threshold">
          <el-input-number 
            v-model="editingRule.threshold" 
            :min="0" 
            :max="100" 
            :precision="2"
          />
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-select v-model="editingRule.severity" placeholder="选择严重程度">
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知渠道" prop="notification_channels">
          <el-checkbox-group v-model="editingRule.notification_channels">
            <el-checkbox label="email">邮件</el-checkbox>
            <el-checkbox label="sms">短信</el-checkbox>
            <el-checkbox label="webhook">Webhook</el-checkbox>
            <el-checkbox label="system">系统通知</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="editingRule.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 告警详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="告警详情"
      width="800px"
    >
      <div class="alert-detail" v-if="selectedAlert">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">{{ selectedAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityType(selectedAlert.severity)">
              {{ getSeverityText(selectedAlert.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="告警内容">{{ selectedAlert.title }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ selectedAlert.source }}</el-descriptions-item>
          <el-descriptions-item label="触发时间">{{ formatTime(selectedAlert.triggered_at) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedAlert.status)">
              {{ getStatusText(selectedAlert.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="详细描述" :span="2">
            {{ selectedAlert.description || '暂无详细描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 告警处理记录 -->
        <div class="alert-actions-history" v-if="selectedAlert.actions">
          <h4>处理记录</h4>
          <el-timeline>
            <el-timeline-item
              v-for="action in selectedAlert.actions"
              :key="action.id"
              :timestamp="formatTime(action.timestamp)"
            >
              <div class="action-content">
                <strong>{{ action.action }}</strong>
                <span>by {{ action.user }}</span>
                <p v-if="action.comment">{{ action.comment }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'

interface AlertRule {
  id?: number
  name: string
  metric: string
  condition: string
  threshold: number
  severity: 'info' | 'warning' | 'critical'
  enabled: boolean
  notification_channels: string[]
  description?: string
}

interface AlertHistory {
  id: number
  severity: 'info' | 'warning' | 'critical'
  title: string
  source: string
  triggered_at: string
  resolved_at?: string
  status: 'active' | 'resolved' | 'ignored'
  description?: string
  actions?: AlertAction[]
}

interface AlertAction {
  id: number
  action: string
  user: string
  timestamp: string
  comment?: string
}

const ruleDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  new Date()
])
const severityFilter = ref('')
const statusFilter = ref('')
const selectedAlerts = ref<AlertHistory[]>([])
const selectedAlert = ref<AlertHistory | null>(null)

// 告警规则数据
const alertRules = ref<AlertRule[]>([
  {
    id: 1,
    name: 'CPU使用率过高',
    metric: 'cpu_usage',
    condition: 'gt',
    threshold: 80,
    severity: 'warning',
    enabled: true,
    notification_channels: ['email', 'system'],
    description: '当CPU使用率超过80%时触发告警'
  },
  {
    id: 2,
    name: '内存使用率严重过高',
    metric: 'memory_usage',
    condition: 'gt',
    threshold: 90,
    severity: 'critical',
    enabled: true,
    notification_channels: ['email', 'sms', 'system'],
    description: '当内存使用率超过90%时触发严重告警'
  },
  {
    id: 3,
    name: '测试失败率过高',
    metric: 'test_failure_rate',
    condition: 'gt',
    threshold: 10,
    severity: 'warning',
    enabled: false,
    notification_channels: ['email'],
    description: '当测试失败率超过10%时触发告警'
  }
])

// 告警历史数据
const alertHistory = ref<AlertHistory[]>([
  {
    id: 1,
    severity: 'warning',
    title: 'CPU使用率持续偏高',
    source: '系统监控',
    triggered_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    status: 'active',
    description: 'CPU使用率在过去10分钟内持续超过80%阈值',
    actions: [
      {
        id: 1,
        action: '告警触发',
        user: '系统',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      }
    ]
  },
  {
    id: 2,
    severity: 'critical',
    title: '数据库连接异常',
    source: '数据库监控',
    triggered_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    resolved_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    status: 'resolved',
    description: '数据库连接池耗尽，无法建立新连接',
    actions: [
      {
        id: 1,
        action: '告警触发',
        user: '系统',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 2,
        action: '问题解决',
        user: '管理员',
        timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        comment: '重启数据库服务，连接恢复正常'
      }
    ]
  }
])

// 编辑中的规则
const editingRule = ref<AlertRule>({
  name: '',
  metric: '',
  condition: '',
  threshold: 0,
  severity: 'info',
  enabled: true,
  notification_channels: []
})

// 表单验证规则
const ruleFormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  metric: [{ required: true, message: '请选择监控指标', trigger: 'change' }],
  condition: [{ required: true, message: '请选择触发条件', trigger: 'change' }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }]
}

// 计算属性
const filteredAlertHistory = computed(() => {
  let filtered = alertHistory.value

  if (severityFilter.value) {
    filtered = filtered.filter(alert => alert.severity === severityFilter.value)
  }

  if (statusFilter.value) {
    filtered = filtered.filter(alert => alert.status === statusFilter.value)
  }

  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    filtered = filtered.filter(alert => {
      const triggeredAt = new Date(alert.triggered_at)
      return triggeredAt >= start && triggeredAt <= end
    })
  }

  return filtered
})

// 方法
const createAlertRule = () => {
  editingRule.value = {
    name: '',
    metric: '',
    condition: '',
    threshold: 0,
    severity: 'info',
    enabled: true,
    notification_channels: []
  }
  ruleDialogVisible.value = true
}

const editRule = (rule: AlertRule) => {
  editingRule.value = { ...rule }
  ruleDialogVisible.value = true
}

const saveRule = async () => {
  try {
    if (editingRule.value.id) {
      // 更新现有规则
      const index = alertRules.value.findIndex(r => r.id === editingRule.value.id)
      if (index !== -1) {
        alertRules.value[index] = { ...editingRule.value }
      }
      ElMessage.success('规则更新成功')
    } else {
      // 创建新规则
      const newRule = {
        ...editingRule.value,
        id: Date.now()
      }
      alertRules.value.push(newRule)
      ElMessage.success('规则创建成功')
    }
    ruleDialogVisible.value = false
  } catch (error) {
    ElMessage.error('保存规则失败')
  }
}

const deleteRule = async (rule: AlertRule) => {
  try {
    await ElMessageBox.confirm('确定要删除这个告警规则吗？', '确认删除', {
      type: 'warning'
    })
    
    const index = alertRules.value.findIndex(r => r.id === rule.id)
    if (index !== -1) {
      alertRules.value.splice(index, 1)
      ElMessage.success('规则删除成功')
    }
  } catch (error) {
    // 用户取消删除
  }
}

const toggleRule = async (rule: AlertRule) => {
  try {
    ElMessage.success(`规则已${rule.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const testRule = async (rule: AlertRule) => {
  ElMessage.info(`正在测试规则: ${rule.name}`)
  // 模拟测试
  setTimeout(() => {
    ElMessage.success('规则测试通过')
  }, 2000)
}

const refreshAlerts = () => {
  ElMessage.success('告警数据已刷新')
}

const filterAlerts = () => {
  // 过滤逻辑已在计算属性中实现
}

const handleSelectionChange = (selection: AlertHistory[]) => {
  selectedAlerts.value = selection
}

const resolveAlert = async (alert: AlertHistory) => {
  try {
    alert.status = 'resolved'
    alert.resolved_at = new Date().toISOString()
    ElMessage.success('告警已解决')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const ignoreAlert = async (alert: AlertHistory) => {
  try {
    alert.status = 'ignored'
    ElMessage.success('告警已忽略')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const viewAlertDetail = (alert: AlertHistory) => {
  selectedAlert.value = alert
  detailDialogVisible.value = true
}

const batchResolve = async () => {
  try {
    selectedAlerts.value.forEach(alert => {
      if (alert.status === 'active') {
        alert.status = 'resolved'
        alert.resolved_at = new Date().toISOString()
      }
    })
    ElMessage.success(`已解决 ${selectedAlerts.value.length} 个告警`)
    selectedAlerts.value = []
  } catch (error) {
    ElMessage.error('批量操作失败')
  }
}

const batchIgnore = async () => {
  try {
    selectedAlerts.value.forEach(alert => {
      if (alert.status === 'active') {
        alert.status = 'ignored'
      }
    })
    ElMessage.success(`已忽略 ${selectedAlerts.value.length} 个告警`)
    selectedAlerts.value = []
  } catch (error) {
    ElMessage.error('批量操作失败')
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedAlerts.value.length} 个告警吗？`, '确认删除', {
      type: 'warning'
    })
    
    const idsToDelete = selectedAlerts.value.map(alert => alert.id)
    alertHistory.value = alertHistory.value.filter(alert => !idsToDelete.includes(alert.id))
    
    ElMessage.success(`已删除 ${selectedAlerts.value.length} 个告警`)
    selectedAlerts.value = []
  } catch (error) {
    // 用户取消删除
  }
}

// 辅助函数
const getSeverityType = (severity: string) => {
  const types: Record<string, string> = {
    'critical': 'danger',
    'warning': 'warning',
    'info': 'info'
  }
  return types[severity] || 'info'
}

const getSeverityText = (severity: string) => {
  const texts: Record<string, string> = {
    'critical': '严重',
    'warning': '警告',
    'info': '信息'
  }
  return texts[severity] || severity
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'active': 'danger',
    'resolved': 'success',
    'ignored': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'active': '活跃',
    'resolved': '已解决',
    'ignored': '已忽略'
  }
  return texts[status] || status
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.alert-manager {
  padding: 20px;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.alert-rules-section,
.alert-history-section {
  margin-bottom: 30px;
}

.alert-rules-section h3,
.alert-history-section h3 {
  margin-bottom: 15px;
  color: #333;
}

.history-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  align-items: center;
}

.batch-actions {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-detail {
  margin-bottom: 20px;
}

.alert-actions-history {
  margin-top: 20px;
}

.alert-actions-history h4 {
  margin-bottom: 15px;
  color: #333;
}

.action-content strong {
  color: #409EFF;
}

.action-content span {
  margin-left: 10px;
  color: #666;
  font-size: 12px;
}

.action-content p {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}
</style>