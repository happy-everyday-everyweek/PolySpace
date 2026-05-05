<template>
  <div class="marketplace-view">
    <div class="mp-header">
      <h2>技能市场</h2>
      <div class="mp-search">
        <input v-model="searchQuery" class="mp-search-input" placeholder="搜索技能..." @input="searchSkills" />
      </div>
    </div>
    <div class="mp-categories">
      <button
        v-for="cat in categories"
        :key="cat.value"
        class="mp-cat-btn"
        :class="{ active: activeCategory === cat.value }"
        @click="activeCategory = cat.value; fetchSkills()"
      >
        {{ cat.label }}
      </button>
    </div>
    <div class="mp-skills-grid">
      <div v-for="skill in skills" :key="skill.id" class="mp-skill-card">
        <div class="skill-icon">{{ categoryIcons[skill.category] || '📦' }}</div>
        <div class="skill-info">
          <h4 class="skill-name">{{ skill.name }}</h4>
          <p class="skill-desc">{{ skill.description }}</p>
          <div class="skill-meta">
            <span class="skill-author">{{ skill.author }}</span>
            <span class="skill-downloads">{{ skill.downloads }} 次安装</span>
            <span class="skill-rating">{{ skill.rating > 0 ? skill.rating.toFixed(1) + ' ★' : '' }}</span>
          </div>
          <div class="skill-tags">
            <span v-for="tag in skill.tags.slice(0, 3)" :key="tag" class="skill-tag">{{ tag }}</span>
          </div>
        </div>
        <div class="skill-actions">
          <button v-if="!isInstalled(skill.id)" class="skill-install-btn" @click="installSkill(skill.id)">
            安装
          </button>
          <button v-else class="skill-installed-btn" @click="uninstallSkill(skill.id)">
            已安装
          </button>
        </div>
      </div>
      <div v-if="!skills.length" class="mp-empty">暂无技能</div>
    </div>
    <div class="mp-installed-section">
      <h3>已安装技能</h3>
      <div class="mp-installed-list">
        <div v-for="skill in installedSkills" :key="skill.id" class="mp-installed-item">
          <span>{{ skill.name }}</span>
          <button class="uninstall-btn" @click="uninstallSkill(skill.id)">卸载</button>
        </div>
        <div v-if="!installedSkills.length" class="mp-empty-sm">尚未安装任何技能</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

interface Skill {
  id: string
  name: string
  description: string
  category: string
  author: string
  downloads: number
  rating: number
  tags: string[]
}

const skills = ref<Skill[]>([])
const installedSkills = ref<Skill[]>([])
const searchQuery = ref('')
const activeCategory = ref('all')
const installedIds = ref<Set<string>>(new Set())

const categories = [
  { label: '全部', value: 'all' },
  { label: '效率', value: 'productivity' },
  { label: '自动化', value: 'automation' },
  { label: '分析', value: 'analysis' },
  { label: '创意', value: 'creative' },
  { label: '开发', value: 'development' },
  { label: '沟通', value: 'communication' },
  { label: '数据', value: 'data' },
  { label: '教育', value: 'education' },
]

const categoryIcons: Record<string, string> = {
  productivity: '⚡', automation: '🤖', analysis: '📊', creative: '🎨',
  development: '💻', communication: '💬', data: '📈', education: '🎓',
}

function isInstalled(id: string) {
  return installedIds.value.has(id)
}

async function fetchSkills() {
  try {
    const params: Record<string, string> = {}
    if (activeCategory.value !== 'all') params.category = activeCategory.value
    if (searchQuery.value) params.search = searchQuery.value
    const { data } = await api.get('/marketplace/skills', { params })
    skills.value = data.skills || []
  } catch { /* ignore */ }
}

async function fetchInstalled() {
  try {
    const { data } = await api.get('/marketplace/installed')
    installedSkills.value = data.skills || []
    installedIds.value = new Set(installedSkills.value.map(s => s.id))
  } catch { /* ignore */ }
}

async function installSkill(id: string) {
  try {
    await api.post(`/marketplace/skills/${id}/install`)
    await fetchInstalled()
    await fetchSkills()
  } catch { /* ignore */ }
}

async function uninstallSkill(id: string) {
  try {
    await api.post(`/marketplace/skills/${id}/uninstall`)
    await fetchInstalled()
    await fetchSkills()
  } catch { /* ignore */ }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
function searchSkills() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchSkills, 300)
}

onMounted(() => {
  fetchSkills()
  fetchInstalled()
})
</script>

<style scoped>
.marketplace-view {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}
.mp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.mp-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0;
}
.mp-search-input {
  padding: 8px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  width: 260px;
  outline: none;
}
.mp-search-input:focus { border-color: var(--accent-color, #6366f1); }
.mp-categories {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.mp-cat-btn {
  padding: 4px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 14px;
  background: transparent;
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 12px;
  cursor: pointer;
}
.mp-cat-btn.active {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.mp-skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.mp-skill-card {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-primary, var(--bg-secondary));
}
.skill-icon {
  font-size: 28px;
  flex-shrink: 0;
}
.skill-info {
  flex: 1;
  min-width: 0;
}
.skill-name {
  font-size: 14px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 4px;
}
.skill-desc {
  font-size: 12px;
  color: var(--text-secondary, var(--text-tertiary));
  margin: 0 0 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.skill-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-secondary, var(--text-tertiary));
  margin-bottom: 6px;
}
.skill-rating { color: #fbbf24; }
.skill-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.skill-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--bg-tertiary, #1e1e3a);
  color: var(--text-secondary, var(--text-tertiary));
}
.skill-actions {
  display: flex;
  align-items: flex-start;
}
.skill-install-btn {
  padding: 4px 14px;
  border: 1px solid var(--accent-color, #6366f1);
  border-radius: 4px;
  background: var(--accent-color, #6366f1);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}
.skill-installed-btn {
  padding: 4px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 4px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 12px;
  cursor: pointer;
}
.mp-installed-section {
  border-top: 1px solid var(--border-color, var(--border-color));
  padding-top: 16px;
}
.mp-installed-section h3 {
  font-size: 16px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 12px;
}
.mp-installed-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mp-installed-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-primary, var(--text-primary));
}
.uninstall-btn {
  padding: 3px 10px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 4px;
  background: none;
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 12px;
  cursor: pointer;
}
.uninstall-btn:hover { color: #f87171; }
.mp-empty, .mp-empty-sm {
  text-align: center;
  color: var(--text-secondary, var(--text-tertiary));
  padding: 20px;
  font-size: 14px;
}
.mp-empty-sm { padding: 10px; }
</style>
