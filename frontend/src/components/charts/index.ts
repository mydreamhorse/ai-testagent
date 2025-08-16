// 数据可视化组件导出
export { default as DefectAnalysisChart } from './DefectAnalysisChart.vue'
export { default as CoverageHeatmap } from './CoverageHeatmap.vue'
export { default as TrendAnalysisChart } from './TrendAnalysisChart.vue'
export { default as StatsDashboard } from './StatsDashboard.vue'

// 组件类型定义
export interface ChartComponentProps {
  title?: string
  data: any[]
  loading?: boolean
}

export interface DefectData {
  id: number
  type: string
  severity: string
  status: string
  detected_at: string
  resolved_at?: string
  description: string
}

export interface CoverageData {
  name: string
  category: string
  coverage: number
  covered_cases: number
  total_cases: number
  missing_areas: string[]
}

export interface TrendDataPoint {
  date: string
  value: number
  change?: number
  change_rate?: number
  notes?: string
}