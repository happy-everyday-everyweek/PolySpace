export const API_BASE = '/api/v1'
export const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`

export const SLASH_COMMANDS = [
  { key: 'settings', label: '设置', description: '打开设置页面' },
  { key: 'clear', label: '清空对话', description: '清空当前对话记录' },
  { key: 'mode', label: '切换模式', description: '在Agent和工作台模式间切换' },
] as const

export const MODEL_TIERS = [
  { key: 'base', label: '基础模型', description: '未配置分级模型时的默认模型' },
  { key: 'strong', label: '强能力模型', description: '负责规划，如GLM-5.1、GPT-5.4' },
  { key: 'performance', label: '高性能模型', description: '负责日常任务，如qwen3.5-35b-a3b' },
  { key: 'cost_effective', label: '性价比模型', description: '负责意图判断、记忆整理等简单任务' },
  { key: 'vertical_multimodal', label: '多模态模型', description: '处理图片、视频、音频等模态' },
  { key: 'vertical_screen', label: '屏幕操作模型', description: '推荐AutoGLM-Phone-9B' },
  { key: 'vertical_custom', label: '自定义垂类模型', description: '用户自定义的垂类模型' },
] as const
