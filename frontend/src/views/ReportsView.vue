<template>
  <div class="reports-view">
    <div class="page-header">
      <h1>测试报告</h1>
      <p>生成和管理各类测试报告</p>
    </div>

    <!-- 报告生成区域 -->
    <div class="report-generation">
      <h2>生成新报告</h2>
      <div class="generation-form">
        <div class="form-group">
          <label for="reportType">报告类型</label>
          <select v-model="newReport.reportType" id="reportType">
            <option value="execution">测试执行报告</option>
            <option value="defect_analysis">缺陷分析报告</option>
            <option value="coverage">覆盖率分析报告</option>
            <option value="trend">趋势分析报告</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="reportTitle">报告标题</label>
          <input 
            v-model="newReport.title" 
            id="reportTitle" 
            type="text" 
            placeholder="输入报告标题"
          />
        </div>
        
        <div class="form-group">
          <label for="dateRange">时间范围</label>
          <div class="date-range">
            <input 
              v-model="newReport.dateRange.start" 
              type="date" 
              placeholder="开始日期"
            />
            <span>至</span>
            <input 
              v-model="newReport.dateRange.end" 
              type="date" 
              placeholder="结束日期"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="exportFormat">导出格式</label>
          <select v-model="newReport.exportFormat" id="exportFormat">
            <option value="">仅在线查看</option>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
            <option value="html">HTML</option>
          </select>
        </div>
        
        <button 
          @click="generateReport" 
          :disabled="isGenerating"
          class="generate-btn"
        >
          {{ isGenerating ? '生成中...' : '生成报告' }}
        </button>
      </div>
    </div>

    <!-- 报告列表 -->
    <div class="reports-list">
      <h2>历史报告</h2>
      
      <div class="filters">
        <select v-model="filters.type">
          <option value="">所有类型</option>
          <option value="execution">测试执行报告</option>
          <option value="defect_analysis">缺陷分析报告</option>
          <option value="coverage">覆盖率分析报告</option>
          <option value="trend">趋势分析报告</option>
        </select>
        
        <select v-model="filters.status">
          <option value="">所有状态</option>
          <option value="generating">生成中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        
        <button @click="loadReports" class="refresh-btn">刷新</button>
      </div>
      
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="reports.length === 0" class="empty-state">
        暂无报告数据
      </div>
      
      <div v-else class="reports-grid">
        <div 
          v-for="report in reports" 
          :key="report.id" 
          class="report-card"
          :class="{ 'generating': report.status === 'generating' }"
        >
          <div class="report-header">
            <h3>{{ report.title }}</h3>
            <span class="report-type">{{ getReportTypeLabel(report.report_type) }}</span>
          </div>
          
          <div class="report-meta">
            <div class="meta-item">
              <span class="label">状态:</span>
              <span class="status" :class="report.status">
                {{ getStatusLabel(report.status) }}
              </span>
            </div>
            <div class="meta-item">
              <span class="label">创建时间:</span>
              <span>{{ formatDate(report.created_at) }}</span>
            </div>
            <div v-if="report.generation_time" class="meta-item">
              <span class="label">生成时间:</span>
              <span>{{ formatDate(report.generation_time) }}</span>
            </div>
          </div>
          
          <div class="report-actions">
            <button 
              v-if="report.status === 'completed'" 
              @click="viewReport(report)"
              class="action-btn view-btn"
            >
              查看报告
            </button>
            <button 
              v-if="report.status === 'completed'" 
              @click="exportReport(report, 'pdf')"
              class="action-btn export-btn"
            >
              导出PDF
            </button>
            <button 
              v-if="report.status === 'completed'" 
              @click="exportReport(report, 'excel')"
              class="action-btn export-btn"
            >
              导出Excel
            </button>
            <button 
              @click="deleteReport(report)"
              class="action-btn delete-btn"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 报告详情模态框 -->
    <div v-if="selectedReport" class="modal-overlay" @click="closeReportModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedReport.title }}</h2>
          <button @click="closeReportModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="report-content">
            <pre v-if="selectedReport.report_data">{{ JSON.stringify(selectedReport.report_data, null, 2) }}</pre>
            <div v-else>报告内容为空</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useNotification } from '@/composables/useNotification'
import { reportsApi } from '@/api/reports'

const { showSuccess, showError } = useNotification()

// 响应式数据
const reports = ref([])
const loading = ref(false)
const isGenerating = ref(false)
const selectedReport = ref(null)

const newReport = reactive({
  reportType: 'execution',
  title: '',
  dateRange: {
    start: '',
    end: ''
  },
  exportFormat: ''
})

const filters = reactive({
  type: '',
  status: ''
})

// 方法
const generateReport = async () => {
  if (!newReport.title.trim()) {
    showError('请输入报告标题')
    return
  }
  
  isGenerating.value = true
  
  try {
    const reportData = {
      report_type: newReport.reportType,
      title: newReport.title,
      data_range_start: newReport.dateRange.start || null,
      data_range_end: newReport.dateRange.end || null,
      export_format: newReport.exportFormat || null
    }
    
    const response = await reportsApi.generateReport(reportData)
    
    if (response.success) {
      showSuccess('报告生成任务已启动')
      // 重置表单
      newReport.title = ''
      newReport.dateRange.start = ''
      newReport.dateRange.end = ''
      newReport.exportFormat = ''
      // 刷新报告列表
      await loadReports()
    } else {
      showError(response.message || '报告生成失败')
    }
  } catch (error) {
    console.error('Generate report error:', error)
    showError('报告生成失败')
  } finally {
    isGenerating.value = false
  }
}

const loadReports = async () => {
  loading.value = true
  
  try {
    const params = {
      skip: 0,
      limit: 50,
      report_type: filters.type || undefined,
      status: filters.status || undefined
    }
    
    const response = await reportsApi.getReports(params)
    
    if (response.success) {
      reports.value = response.data.reports || []
    } else {
      showError(response.message || '加载报告列表失败')
    }
  } catch (error) {
    console.error('Load reports error:', error)
    showError('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

const viewReport = (report) => {
  selectedReport.value = report
}

const closeReportModal = () => {
  selectedReport.value = null
}

const exportReport = async (report, format) => {
  try {
    const response = await reportsApi.exportReport(report.id, format)
    
    if (response.success) {
      showSuccess(`报告导出成功: ${format.toUpperCase()}`)
      // 这里可以添加下载逻辑
      if (response.data.download_url) {
        window.open(response.data.download_url, '_blank')
      }
    } else {
      showError(response.message || '报告导出失败')
    }
  } catch (error) {
    console.error('Export report error:', error)
    showError('报告导出失败')
  }
}

const deleteReport = async (report) => {
  if (!confirm(`确定要删除报告"${report.title}"吗？`)) {
    return
  }
  
  try {
    const response = await reportsApi.deleteReport(report.id)
    
    if (response.success) {
      showSuccess('报告删除成功')
      await loadReports()
    } else {
      showError(response.message || '报告删除失败')
    }
  } catch (error) {
    console.error('Delete report error:', error)
    showError('报告删除失败')
  }
}

// 辅助方法
const getReportTypeLabel = (type) => {
  const labels = {
    execution: '测试执行报告',
    defect_analysis: '缺陷分析报告',
    coverage: '覆盖率分析报告',
    trend: '趋势分析报告'
  }
  return labels[type] || type
}

const getStatusLabel = (status) => {
  const labels = {
    generating: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-header p {
  color: #7f8c8d;
  margin: 0;
}

.report-generation {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.report-generation h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.generation-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #34495e;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-range input {
  flex: 1;
}

.generate-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.generate-btn:hover:not(:disabled) {
  background: #2980b9;
}

.generate-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.reports-list {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.reports-list h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.filters select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.refresh-btn {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #7f8c8d;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.report-card {
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 20px;
  transition: box-shadow 0.2s;
}

.report-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.report-card.generating {
  border-color: #f39c12;
  background: #fef9e7;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.report-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}

.report-type {
  background: #ecf0f1;
  color: #34495e;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.report-meta {
  margin-bottom: 15px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
}

.meta-item .label {
  color: #7f8c8d;
}

.status {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.status.generating {
  background: #f39c12;
  color: white;
}

.status.completed {
  background: #27ae60;
  color: white;
}

.status.failed {
  background: #e74c3c;
  color: white;
}

.report-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.view-btn {
  background: #3498db;
  color: white;
}

.view-btn:hover {
  background: #2980b9;
}

.export-btn {
  background: #95a5a6;
  color: white;
}

.export-btn:hover {
  background: #7f8c8d;
}

.delete-btn {
  background: #e74c3c;
  color: white;
}

.delete-btn:hover {
  background: #c0392b;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e1e8ed;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.report-content pre {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.4;
}
</style>