<template>
  <div class="asset-library">
    <div class="section">
      <div class="section-header">
        <span class="section-title">素材包</span>
        <button class="import-btn" @click="triggerImport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          导入ZIP
        </button>
      </div>
      <div v-if="packs.length === 0" class="empty-hint">暂无素材包，导入ZIP压缩包添加素材</div>
      <div v-for="pack in packs" :key="pack.packId" class="pack-card">
        <div class="pack-info">
          <span class="pack-name">{{ pack.name }}</span>
          <span class="pack-count">{{ pack.itemCount }} 项</span>
        </div>
        <div class="pack-items">
          <div v-for="item in pack.items" :key="item.id" class="asset-item" :title="item.name" @click="useAsset(item)">
            <div class="asset-thumb">
              <svg v-if="item.type === 'sticker'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>
              <svg v-else-if="item.type === 'music'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
            </div>
            <span class="asset-name">{{ item.name }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="section-title">ZIP 素材包格式</div>
      <div class="format-hint">
        <p>ZIP根目录需包含 manifest.json:</p>
        <pre>{ "name": "素材包名",
  "items": [{
    "name": "素材名",
    "type": "sticker|music|effect|font|background",
    "src": "file.png",
    "tags": ["标签"]
  }]
}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AssetPack, AssetItem } from '../../../composables/useEditorCore'

defineProps<{ packs: AssetPack[] }>()
const emit = defineEmits<{ 'import-pack': [zipPath: string] }>()

function triggerImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.zip'
  input.onchange = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) emit('import-pack', file.name)
  }
  input.click()
}

function useAsset(_item: AssetItem) {
}
</script>

<style scoped>
.asset-library { padding: 12px; }
.section { margin-bottom: 16px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.section-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.import-btn { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border: 1px solid var(--primary); background: transparent; color: var(--primary); border-radius: 4px; cursor: pointer; font-size: 11px; }
.import-btn:hover { background: var(--primary-light); }
.empty-hint { text-align: center; color: var(--text-tertiary); padding: 20px 0; font-size: 12px; }
.pack-card { border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; margin-bottom: 8px; background: var(--bg-primary); }
.pack-info { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.pack-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.pack-count { font-size: 11px; color: var(--text-tertiary); }
.pack-items { display: flex; flex-wrap: wrap; gap: 6px; }
.asset-item { display: flex; flex-direction: column; align-items: center; gap: 4px; width: 56px; padding: 6px 2px; border-radius: 4px; cursor: pointer; transition: background 0.15s; }
.asset-item:hover { background: var(--bg-tertiary); }
.asset-thumb { width: 36px; height: 36px; border-radius: 4px; background: var(--bg-tertiary); display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); }
.asset-name { font-size: 9px; color: var(--text-secondary); text-align: center; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 52px; }
.format-hint { background: var(--bg-tertiary); border-radius: 4px; padding: 10px; }
.format-hint p { font-size: 11px; color: var(--text-secondary); margin-bottom: 6px; }
.format-hint pre { font-size: 10px; color: var(--text-tertiary); white-space: pre-wrap; word-break: break-all; }
</style>
