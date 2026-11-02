import ReactECharts from 'echarts-for-react'
import { useApp } from '../hooks/AppContext'

export default function EChart({ option, height = 320 }: { option: any; height?: number }) {
  const { theme } = useApp()
  const merged = {
    textStyle: { fontFamily: 'Inter, sans-serif' },
    backgroundColor: 'transparent',
    ...option,
  }
  return (
    <ReactECharts
      option={merged}
      theme={theme === 'dark' ? 'dark' : undefined}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'svg' }}
      notMerge
    />
  )
}
