export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
}

export interface Requirement {
  id: number
  title: string
  description: string
  content: string
  file_path?: string
  file_type?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  user_id: number
  created_at: string
  updated_at: string
}

export interface ParsedFeature {
  id: number
  requirement_id: number
  feature_name: string
  feature_type: string
  description?: string
  parameters?: Record<string, any>
  constraints?: Record<string, any>
  dependencies?: string[]
  priority: 'high' | 'medium' | 'low'
  created_at: string
}

export interface TestCase {
  id: number
  requirement_id: number
  user_id: number
  title: string
  description?: string
  test_type: 'function' | 'boundary' | 'exception' | 'performance' | 'security'
  preconditions?: string
  test_steps: string
  expected_result: string
  priority: 'high' | 'medium' | 'low'
  status: string
  generated_by: string
  template_id?: string
  created_at: string
  updated_at: string
}

export interface TestCaseEvaluation {
  id: number
  test_case_id: number
  completeness_score: number
  accuracy_score: number
  executability_score: number
  coverage_score: number
  clarity_score: number
  total_score: number
  evaluation_details?: Record<string, any>
  suggestions?: string[]
  evaluator_type: string
  evaluated_at: string
}

export interface TestTemplate {
  id: number
  name: string
  category: string
  description?: string
  template_content: string
  variables?: Record<string, any>
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface KnowledgeBase {
  id: number
  category: string
  subcategory?: string
  title: string
  content: string
  tags?: string[]
  source?: string
  confidence: number
  usage_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface GenerationRequest {
  requirement_id: number
  generation_type: string
  options?: Record<string, any>
}

export interface GenerationResponse {
  task_id: string
  status: string
  message: string
  estimated_time?: number
}

export interface FileUploadResponse {
  filename: string
  file_path: string
  file_size: number
  file_type: string
  upload_time: string
}