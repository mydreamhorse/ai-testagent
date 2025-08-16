<template>
  <div class="monitoring-view">
    <div class="page-header">
      <h2>系统监控</h2>
      <div class="header-actions">
        <el-button @click="refreshAllData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
          全屏模式
        </el-button>
        <el-button @click="showSettings = true">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </div>

    <!-- Real-time Metrics -->
    <div class="metrics-section">
      <RealTimeMetrics
        :showThresholdSettings="false"
        @thresholdUpdate="handleThresholdUpdate"
      />
    </div>

    <!-- Monitoring Dashboard -->
    <div class="dashboard-section">
      <MonitoringDashboard />
    </div>

    <!-- Alert Manager -->
    <div class="alerts-section">
      <AlertManager />
    </div>

    <!-- Settings Dialog -->
    <el-dialog
      v-model="showSettings"
      title="监控设置"
      width="800px"
    >
      <el-tabs v-model="activeSettingsTab">
        <el-tab-pane label="告警阈值" name="thresholds">
          <div class="settings-content">
            <h4>系统指标阈值</h4>
            <el-form :model="thresholdSettings" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="CPU使用率">
                    <div class="threshold-inputs">
                      <el-input-number 
                        v-model="thresholdSettings.cpu_warning" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (警告)</span>
                      <el-input-number 
                        v-model="thresholdSettings.cpu_critical" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (严重)</span>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="内存使用率">
                    <div class="threshold-inputs">
                      <el-input-number 
                        v-model="thresholdSettings.memory_warning" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (警告)</span>
                      <el-input-number 
                        v-model="thresholdSettings.memory_critical" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (严重)</span>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="响应时间">
                    <div class="threshold-inputs">
                      <el-input-number 
                        v-model="thresholdSettings.response_warning" 
                        :min="0" 
                        :precision="0"
                      />
                      <span>ms (警告)</span>
                      <el-input-number 
                        v-model="thresholdSettings.response_critical" 
                        :min="0" 
                        :precision="0"
                      />
                      <span>ms (严重)</span>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="错误率">
                    <div class="threshold-inputs">
                      <el-input-number 
                        v-model="thresholdSettings.error_warning" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (警告)</span>
                      <el-input-number 
                        v-model="thresholdSettings.error_critical" 
                        :min="0" 
                        :max="100" 
                        :precision="1"
                      />
                      <span>% (严重)</span>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="通知设置" name="notifications">
          <div class="settings-content">
            <h4>通知渠道配置</h4>
            <el-form :model="notificationSettings" label-width="120px">
              <el-form-item label="邮件通知">
                <el-switch v-model="notificationSettings.email_enabled" />
                <el-input 
                  v-if="notificationSettings.email_enabled"
                  v-model="notificationSettings.email_recipients"
                  placeholder="多个邮箱用逗号分隔"
                  style="margin-left: 10px; width: 300px;"
                />
              </el-form-item>
              <el-form-item label="短信通知">
                <el-switch v-model="notificationSettings.sms_enabled" />
                <el-input 
                  v-if="notificationSettings.sms_enabled"
                  v-model="notificationSettings.sms_recipients"
                  placeholder="多个手机号用逗号分隔"
                  style="margin-left: 10px; width: 300px;"
                />
              </el-form-item>
              <el-form-item label="Webhook">
                <el-switch v-model="notificationSettings.webhook_enabled" />
                <el-input 
                  v-if="notificationSettings.webhook_enabled"
                  v-model="notificationSettings.webhook_url"
                  placeholder="Webhook URL"
                  style="margin-left: 10px; width: 300px;"
                />
              </el-form-item>
              <el-form-item label="系统通知">
                <el-switch v-model="notificationSettings.system_enabled" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="数据保留" name="retention">
          <div class="settings-content">
            <h4>数据保留策略</h4>
            <el-form :model="retentionSettings" label-width="120px">
              <el-form-item label="监控数据">
                <el-select v-model="retentionSettings.metrics_retention">
                  <el-option label="7天" value="7d" />
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                  <el-option label="1年" value="1y" />
                </el-select>
              </el-form-item>
              <el-form-item label="告警历史">
                <el-select v-model="retentionSettings.alerts_retention">
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                  <el-option label="1年" value="1y" />
                  <el-option label="永久" value="forever" />
                </el-select>
              </el-form-item>
              <el-form-item label="系统日志">
                <el-select v-model="retentionSettings.logs_retention">
                  <el-option label="7天" value="7d" />
                  <el-option label="30天" value="30d" />
                  <el-option label="90天" value="90d" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, 
  FullScreen, 
  Setting 
} from '@element-plus/icons-vue'
import RealTimeMetrics from '@/components/monitoring/RealTimeMetrics.vue'
import MonitoringDashboard from '@/components/monitoring/MonitoringDashboard.vue'
import AlertManager from '@/components/monitoring/AlertManager.vue'

interface ThresholdSettings {
  cpu_warning: number
  cpu_critical: number
  memory_warning: number
  memory_critical: number
  response_warning: number
  response_critical: number
  error_warning: number
  error_critical: number
}

interface NotificationSettings {
  email_enabled: boolean
  email_recipients: string
  sms_enabled: boolean
  sms_recipients: string
  webhook_enabled: boolean
  webhook_url: string
  system_enabled: boolean
}

interface RetentionSettings {
  metrics_retention: string
  alerts_retention: string
  logs_retention: string
}

const loading = ref(false)
const showSettings = ref(false)
const activeSettingsTab = ref('thresholds')

// Settings data
const thresholdSettings = ref<ThresholdSettings>({
  cpu_warning: 70,
  cpu_critical: 90,
  memory_warning: 80,
  memory_critical: 95,
  response_warning: 500,
  response_critical: 1000,
  error_warning: 5,
  error_critical: 10
})

const notificationSettings = ref<NotificationSettings>({
  email_enabled: true,
  email_recipients: 'admin@example.com',
  sms_enabled: false,
  sms_recipients: '',
  webhook_enabled: false,
  webhook_url: '',
  system_enabled: true
})

const retentionSettings = ref<RetentionSettings>({
  metrics_retention: '30d',
  alerts_retention: '90d',
  logs_retention: '7d'
})

// Methods
const refreshAllData = async () => {
  loading.value = true
  try {
    // Simulate data refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('所有监控数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    ElMessage.info('已进入全屏模式')
  } else {
    document.exitFullscreen()
    ElMessage.info('已退出全屏模式')
  }
}

const handleThresholdUpdate = (thresholds: any) => {
  Object.assign(thresholdSettings.value, thresholds)
  ElMessage.success('阈值设置已更新')
}

const saveSettings = async () => {
  try {
    // Save settings to backend
    await new Promise(resolve => setTimeout(resolve, 500))
    
    ElMessage.success('设置保存成功')
    showSettings.value = false
  } catch (error) {
    ElMessage.error('保存设置失败')
  }
}

const loadSettings = async () => {
  try {
    // Load settings from backend
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Update settings with loaded data
    // thresholdSettings.value = loadedThresholds
    // notificationSettings.value = loadedNotifications
    // retentionSettings.value = loadedRetention
  } catch (error) {
    console.error('Failed to load settings', error)
  }
}

// Keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'F11') {
    event.preventDefault()
    toggleFullscreen()
  } else if (event.ctrlKey && event.key === 'r') {
    event.preventDefault()
    refreshAllData()
  }
}

// Lifecycle
onMounted(() => {
  loadSettings()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.monitoring-view {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.metrics-section,
.dashboard-section,
.alerts-section {
  margin-bottom: 20px;
}

.settings-content {
  padding: 20px 0;
}

.settings-content h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-weight: 600;
}

.threshold-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.threshold-inputs span {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* Fullscreen styles */
:fullscreen .monitoring-view {
  padding: 10px;
}

:fullscreen .page-header {
  margin-bottom: 10px;
  padding: 10px 20px;
}

:fullscreen .metrics-section,
:fullscreen .dashboard-section,
:fullscreen .alerts-section {
  margin-bottom: 10px;
}
</style>