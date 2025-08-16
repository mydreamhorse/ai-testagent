import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElCard, ElSelect, ElDatePicker, ElTable } from 'element-plus'
import TrendAnalysisChart from '../TrendAnalysisChart.vue'

// Mock vue-echarts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="mock-trend-chart"></div>',
    props: ['option', 'loading']
  }
}))

const mockTrendData = [
  {
    date: '2024-01-10',
    value: 75,
    change: 0,
    change_rate: 0,
    notes: '基准数据'
  },
  {
    date: '2024-01-11',
    value: 78,
    change: 3,
    change_rate: 4.0,
    notes: '轻微上升'
  },
  {
    date: '2024-01-12',
    value: 82,
    change: 4,
    change_rate: 5.1,
    notes: '持续改善'
  },
  {
    date: '2024-01-13',
    value: 79,
    change: -3,
    change_rate: -3.7,
    notes: '小幅回落'
  },
  {
    date: '2024-01-14',
    value: 85,
    change: 6,
    change_rate: 7.6,
    notes: '显著提升'
  }
]

describe('TrendAnalysisChart', () => {
  it('renders correctly with data', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        title: '趋势分析图表',
        data: mockTrendData,
        loading: false
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    expect(wrapper.find('.trend-analysis-chart').exists()).toBe(true)
    expect(wrapper.text()).toContain('趋势分析图表')
  })

  it('calculates trend indicator correctly', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    const indicator = vm.trendIndicator
    
    // 从75到85，上升13.3%，应该是上升趋势
    expect(indicator.type).toBe('up')
    expect(indicator.text).toContain('上升')
  })

  it('generates prediction correctly', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    const prediction = vm.prediction
    
    expect(prediction.value).toBeDefined()
    expect(prediction.description).toContain('预计7天后')
  })

  it('provides appropriate recommendations', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    const recommendations = vm.recommendations
    
    expect(Array.isArray(recommendations)).toBe(true)
    expect(recommendations.length).toBeGreaterThan(0)
    
    // 由于是上升趋势，应该包含保持相关的建议
    const hasKeepRecommendation = recommendations.some((rec: string) => 
      rec.includes('保持') || rec.includes('良好')
    )
    expect(hasKeepRecommendation).toBe(true)
  })

  it('switches trend types correctly', async () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const select = wrapper.findComponent(ElSelect)
    if (select.exists()) {
      await select.vm.$emit('update:modelValue', 'defects')
      expect(wrapper.vm.trendType).toBe('defects')
    }
  })

  it('handles date range changes', async () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const datePicker = wrapper.findComponent(ElDatePicker)
    if (datePicker.exists()) {
      const newRange: [Date, Date] = [new Date('2024-01-01'), new Date('2024-01-15')]
      await datePicker.vm.$emit('change', newRange)
      expect(wrapper.emitted('dateRangeChange')).toBeTruthy()
    }
  })

  it('calculates moving average correctly', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    const values = [75, 78, 82, 79, 85]
    const movingAvg = vm.calculateMovingAverage(values, 3)
    
    // 前两个值应该是null（窗口大小为3）
    expect(movingAvg[0]).toBeNull()
    expect(movingAvg[1]).toBeNull()
    
    // 第三个值应该是前三个数的平均值
    expect(movingAvg[2]).toBeCloseTo((75 + 78 + 82) / 3, 1)
  })

  it('displays trend details table', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const table = wrapper.findComponent(ElTable)
    expect(table.exists()).toBe(true)
  })

  it('handles insufficient data gracefully', () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: [{ date: '2024-01-01', value: 50 }] // 只有一个数据点
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    const indicator = vm.trendIndicator
    const prediction = vm.prediction
    
    expect(indicator.type).toBe('stable')
    expect(indicator.text).toContain('数据不足')
    expect(prediction.value).toBe('无法预测')
  })

  it('emits export event when export button is clicked', async () => {
    const wrapper = mount(TrendAnalysisChart, {
      props: {
        data: mockTrendData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElDatePicker,
          ElTable
        }
      }
    })

    const exportButton = wrapper.find('[data-testid="export-button"]')
    if (exportButton.exists()) {
      await exportButton.trigger('click')
      expect(wrapper.emitted('exportData')).toBeTruthy()
    }
  })
})