import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import type {
  WeatherAppSettings,
  EmailAppSettings,
  ScreenRecorderAppSettings,
  PptAppSettings,
  PdfAppSettings,
  VideoAppSettings,
  ImageAppSettings,
  DocumentAppSettings,
  FocusTimerAppSettings,
} from '@/types/settings'

type AppKey = 'weather' | 'email' | 'screenRecorder' | 'ppt' | 'pdf' | 'video' | 'image' | 'document' | 'focusTimer'

type AppSettingsType<K extends AppKey> =
  K extends 'weather' ? WeatherAppSettings :
  K extends 'email' ? EmailAppSettings :
  K extends 'screenRecorder' ? ScreenRecorderAppSettings :
  K extends 'ppt' ? PptAppSettings :
  K extends 'pdf' ? PdfAppSettings :
  K extends 'video' ? VideoAppSettings :
  K extends 'image' ? ImageAppSettings :
  K extends 'document' ? DocumentAppSettings :
  K extends 'focusTimer' ? FocusTimerAppSettings :
  never

export function useAppSettings<K extends AppKey>(appKey: K) {
  const settingsStore = useSettingsStore()

  const appSettings = computed<AppSettingsType<K>>(() => {
    return settingsStore.settings.app[appKey] as AppSettingsType<K>
  })

  return {
    settings: appSettings,
  }
}
