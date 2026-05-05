<template>
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <template v-if="type === 'wechat'">
      <path d="M8.5 2C5.46 2 3 4.46 3 7.5c0 1.68.75 3.18 1.94 4.19L4 14l2.6-1.3c.6.19 1.24.3 1.9.3.34 0 .67-.03 1-.09"/>
      <path d="M15.5 8c-3.04 0-5.5 2.46-5.5 5.5 0 3.04 2.46 5.5 5.5 5.5.66 0 1.3-.11 1.9-.3L20 20l-.94-2.31A5.47 5.47 0 0021 13.5C21 10.46 18.54 8 15.5 8z"/>
      <circle cx="7" cy="7" r="0.5" fill="currentColor"/>
      <circle cx="10" cy="7" r="0.5" fill="currentColor"/>
      <circle cx="14" cy="13" r="0.5" fill="currentColor"/>
      <circle cx="17" cy="13" r="0.5" fill="currentColor"/>
    </template>
    <template v-else-if="type === 'telegram'">
      <circle cx="12" cy="12" r="10"/>
      <path d="M8 12l2.5 2.5L17 8"/>
    </template>
    <template v-else-if="type === 'discord'">
      <path d="M9 12a1 1 0 100-2 1 1 0 000 2z"/>
      <path d="M15 12a1 1 0 100-2 1 1 0 000 2z"/>
      <path d="M7.5 7.5C9 6 10.5 5.5 12 5.5s3 .5 4.5 2"/>
      <path d="M16.5 16.5C15 18 13.5 18.5 12 18.5s-3-.5-4.5-2"/>
      <path d="M5 8c0-1 .5-2 1.5-2.5"/>
      <path d="M19 8c0-1-.5-2-1.5-2.5"/>
      <path d="M5 16c0 1 .5 2 1.5 2.5"/>
      <path d="M19 16c0 1-.5 2-1.5 2.5"/>
    </template>
    <template v-else-if="type === 'slack'">
      <rect x="2" y="10" width="4" height="4" rx="1"/>
      <rect x="10" y="2" width="4" height="4" rx="1"/>
      <rect x="10" y="10" width="4" height="4" rx="1"/>
      <rect x="18" y="10" width="4" height="4" rx="1"/>
      <rect x="10" y="18" width="4" height="4" rx="1"/>
      <line x1="6" y1="12" x2="10" y2="12"/>
      <line x1="14" y1="12" x2="18" y2="12"/>
      <line x1="12" y1="6" x2="12" y2="10"/>
      <line x1="12" y1="14" x2="12" y2="18"/>
    </template>
    <template v-else-if="type === 'feishu'">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
      <path d="M2 17l10 5 10-5"/>
      <path d="M2 12l10 5 10-5"/>
    </template>
    <template v-else-if="type === 'wecom'">
      <rect x="3" y="3" width="18" height="18" rx="3"/>
      <path d="M8 9h8"/>
      <path d="M8 12h5"/>
      <path d="M8 15h6"/>
      <circle cx="18" cy="18" r="4" fill="var(--bg-primary, #1a1a2e)" stroke="currentColor"/>
      <path d="M16.5 18l1 1 2-2"/>
    </template>
    <template v-else-if="type === 'dingtalk'">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
      <path d="M8 13c0-2.5 2-5 4-5s4 2.5 4 5"/>
      <path d="M7 10l2 1"/>
      <path d="M17 10l-2 1"/>
      <path d="M10 16h4"/>
    </template>
    <template v-else>
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
    </template>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ type: string }>()
</script>
