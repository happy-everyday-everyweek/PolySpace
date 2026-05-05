<template>
  <div class="settings-dialog">
    <div class="settings-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="settings-content">
      <OverviewSettings v-if="activeTab === 'overview'" />
      <GeneralSettings v-if="activeTab === 'general'" />
      <AgentSettings v-if="activeTab === 'agent'" />
      <AppSettings v-if="activeTab === 'app'" />
      <ProactiveSettings v-if="activeTab === 'proactive'" />
      <DistributedSettings v-if="activeTab === 'distributed'" />
      <AuditSettings v-if="activeTab === 'audit'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import OverviewSettings from './OverviewSettings.vue'
import GeneralSettings from './GeneralSettings.vue'
import AgentSettings from './AgentSettings.vue'
import AppSettings from './AppSettings.vue'
import ProactiveSettings from './ProactiveSettings.vue'
import DistributedSettings from './DistributedSettings.vue'
import AuditSettings from './AuditSettings.vue'

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'general', label: '通用' },
  { key: 'agent', label: 'AI Agent' },
  { key: 'app', label: '应用' },
  { key: 'proactive', label: '主动式' },
  { key: 'distributed', label: '分布式' },
  { key: 'audit', label: '审计日志' },
]

const activeTab = ref('overview')
</script>

<style scoped>
.settings-dialog {
  display: flex;
  height: 100%;
}

.settings-tabs {
  width: 180px;
  border-right: 1px solid var(--border-color);
  padding: var(--spacing-lg) var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--bg-secondary);
}

.tab-btn {
  text-align: left;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background: var(--border-color);
  color: var(--text-color);
}

.tab-btn.active {
  background: var(--primary-light);
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
}

.settings-content {
  flex: 1;
  padding: var(--spacing-xl);
  overflow-y: auto;
}
</style>
