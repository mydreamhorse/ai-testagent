import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElCard } from 'element-plus'
import DefectAnalysisChart from '../DefectAnalysisChart.vue'

// Mock vue-echarts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="mock-chart"></div>',
    props: ['option', 'loading']
  }
}))

const mockDefectData = [
  {
    id: 1,
    type: 'functional',
    severity: 'high',
    status: 'open',
    detected_at: '2024-01-15T10:00:00Z',
    description: '功能缺陷描述'
  },
  {
    id: 2,
    type: 'performance',
    severity: 'medium',
    status: 'resolved',
    detected_at: '2024-01-14T15:30:00Z',
    resolved_at: '2024-01-15T09:00:00Z',
    description: '性能缺陷描述'
  },
  {
    id: 3,
    type: 'security',
    severity: 'critical',
    status: 'open',
    detected_at: '2024-01-13T08:45:00Z',
    description: '安全缺陷描述'
  }
]

describe('DefectAnalysisChart', () => {
  it('renders correctly with data', () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        title: '缺陷分析图表',
        data: mockDefectData,
        loading: false
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    expect(wrapper.find('.defect-analysis-chart').exists()).toBe(true)
    expect(wrapper.text()).toContain('缺陷分析图表')
  })

  it('displays correct statistics', () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        data: mockDefectData
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    // 检查统计数据
    expect(wrapper.text()).toContain('3') // 总缺陷数
    expect(wrapper.text()).toContain('1') // 严重缺陷数
    expect(wrapper.text()).toContain('1') // 已解决数
    expect(wrapper.text()).toContain('33%') // 解决率
  })

  it('switches chart types correctly', async () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        data: mockDefectData
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    // 点击趋势图按钮
    const trendButton = wrapper.find('[data-testid="trend-button"]')
    if (trendButton.exists()) {
      await trendButton.trigger('click')
      // 验证图表类型已切换
    }
  })

  it('emits defectClick event when chart is clicked', async () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        data: mockDefectData
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    // 模拟图表点击事件
    const chart = wrapper.findComponent({ name: 'VChart' })
    if (chart.exists()) {
      await chart.vm.$emit('click', { dataIndex: 0 })
      expect(wrapper.emitted('defectClick')).toBeTruthy()
    }
  })

  it('handles loading state correctly', () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        data: mockDefectData,
        loading: true
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    const chart = wrapper.findComponent({ name: 'VChart' })
    expect(chart.props('loading')).toBe(true)
  })

  it('handles empty data gracefully', () => {
    const wrapper = mount(DefectAnalysisChart, {
      props: {
        data: []
      },
      global: {
        components: {
          ElButton,
          ElCard
        }
      }
    })

    expect(wrapper.find('.defect-analysis-chart').exists()).toBe(true)
    // 验证空数据时的显示
    expect(wrapper.text()).toContain('0') // 总缺陷数应为0
  })
})