import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton, ElCard, ElSelect, ElTable } from 'element-plus'
import CoverageHeatmap from '../CoverageHeatmap.vue'

// Mock vue-echarts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    template: '<div class="mock-heatmap"></div>',
    props: ['option', 'loading']
  }
}))

const mockCoverageData = [
  {
    name: '座椅调节',
    category: '核心功能',
    coverage: 85,
    covered_cases: 17,
    total_cases: 20,
    missing_areas: ['边界测试', '异常处理']
  },
  {
    name: '加热功能',
    category: '辅助功能',
    coverage: 92,
    covered_cases: 23,
    total_cases: 25,
    missing_areas: ['温度控制']
  },
  {
    name: '记忆功能',
    category: '高级功能',
    coverage: 65,
    covered_cases: 13,
    total_cases: 20,
    missing_areas: ['多用户场景', '数据持久化', '故障恢复']
  }
]

describe('CoverageHeatmap', () => {
  it('renders correctly with data', () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        title: '覆盖率热力图',
        data: mockCoverageData,
        loading: false
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    expect(wrapper.find('.coverage-heatmap').exists()).toBe(true)
    expect(wrapper.text()).toContain('覆盖率热力图')
  })

  it('calculates coverage statistics correctly', () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: mockCoverageData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    // 检查统计数据计算
    const vm = wrapper.vm as any
    const stats = vm.coverageStats
    
    expect(stats.overall).toBe(81) // (85+92+65)/3 ≈ 81
    expect(stats.high_coverage).toBe(67) // 2/3 * 100 ≈ 67% (85%, 92% >= 70%)
    expect(stats.low_coverage).toBe(0) // 0/3 * 100 = 0% (none < 30%)
  })

  it('switches view modes correctly', async () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: mockCoverageData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    const select = wrapper.findComponent(ElSelect)
    if (select.exists()) {
      await select.vm.$emit('update:modelValue', 'function')
      expect(wrapper.vm.viewMode).toBe('function')
    }
  })

  it('displays coverage details table', () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: mockCoverageData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    // 检查详情表格是否显示
    const table = wrapper.findComponent(ElTable)
    expect(table.exists()).toBe(true)
  })

  it('emits cellClick event when heatmap cell is clicked', async () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: mockCoverageData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    const chart = wrapper.findComponent({ name: 'VChart' })
    if (chart.exists()) {
      await chart.vm.$emit('click', { data: [0, 0, 85] })
      expect(wrapper.emitted('cellClick')).toBeTruthy()
    }
  })

  it('shows correct coverage colors', () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: mockCoverageData
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    const vm = wrapper.vm as any
    
    // 测试覆盖率颜色函数
    expect(vm.getCoverageColor(95)).toBe('#389e0d') // 90-100%
    expect(vm.getCoverageColor(75)).toBe('#52c41a') // 70-90%
    expect(vm.getCoverageColor(55)).toBe('#ffa940') // 50-70%
    expect(vm.getCoverageColor(35)).toBe('#ff7a45') // 30-50%
    expect(vm.getCoverageColor(15)).toBe('#ff4d4f') // 0-30%
  })

  it('handles empty data gracefully', () => {
    const wrapper = mount(CoverageHeatmap, {
      props: {
        data: []
      },
      global: {
        components: {
          ElButton,
          ElCard,
          ElSelect,
          ElTable
        }
      }
    })

    expect(wrapper.find('.coverage-heatmap').exists()).toBe(true)
    
    const vm = wrapper.vm as any
    const stats = vm.coverageStats
    expect(stats.overall).toBe(0)
    expect(stats.high_coverage).toBe(0)
    expect(stats.medium_coverage).toBe(0)
    expect(stats.low_coverage).toBe(0)
  })
})