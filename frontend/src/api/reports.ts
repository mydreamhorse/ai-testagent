import apiClient from './index'

export interface ReportGenerationRequest {
  report_type: 'execution' | 'defect_analysis' | 'coverage' | 'trend'
  title: string
  data_range_start?: string | null
  data_range_end?: string | null
  export_format?: 'pdf' | 'excel' | 'html' | null
  filters?: Record<string, any>
}

export interface Report {
  id: number
  title: string
  report_type: string
  generated_by: number
  generation_time: string
  report_data: any
  file_path?: string
  status: 'generating' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface ReportsListParams {
  skip?: number
  limit?: number
  report_type?: string
  status?: string
}

export const reportsApi = {
  // 获取报告列表
  async getReports(params: ReportsListParams = {}) {
    const response = await apiClient.get('/api/v1/reports/', { params })
    return response
  },

  // 获取单个报告详情
  async getReport(reportId: number) {
    const response = await apiClient.get(`/api/v1/reports/${reportId}`)
    return response
  },

  // 生成报告
  async generateReport(data: ReportGenerationRequest) {
    const response = await apiClient.post('/api/v1/reports/generate', data)
    return response
  },

  // 导出报告
  async exportReport(reportId: number, format: 'pdf' | 'excel' | 'html') {
    const response = await apiClient.get(`/api/v1/reports/${reportId}/export`, {
      params: { format }
    })
    return response
  },

  // 删除报告
  async deleteReport(reportId: number) {
    const response = await apiClient.delete(`/api/v1/reports/${reportId}`)
    return response
  },

  // 分享报告
  async shareReport(data: {
    report_id: number
    share_with_users?: number[]
    share_via_email?: string[]
    share_via_link?: boolean
    expiry_date?: string
  }) {
    const response = await apiClient.post('/api/v1/reports/share', data)
    return response
  }
}