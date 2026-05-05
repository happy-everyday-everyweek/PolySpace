import { ref, computed } from 'vue'
import zhCN from '@/locales/zh-CN'
import enUS from '@/locales/en-US'

const messages: Record<string, any> = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

const currentLocale = ref('zh-CN')

export function useI18n() {
  const t = (key: string): string => {
    const keys = key.split('.')
    let value = messages[currentLocale.value]
    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        return key
      }
    }
    return typeof value === 'string' ? value : key
  }

  const locale = computed({
    get: () => currentLocale.value,
    set: (val: string) => {
      currentLocale.value = val
      localStorage.setItem('locale', val)
    }
  })

  function initLocale() {
    const saved = localStorage.getItem('locale')
    if (saved && messages[saved]) {
      currentLocale.value = saved
    } else {
      const browserLang = navigator.language
      currentLocale.value = messages[browserLang] ? browserLang : 'zh-CN'
    }
  }

  return { t, locale, initLocale }
}
