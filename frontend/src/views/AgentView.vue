<template>
  <div class="agent-view">
    <ChatPanel />
  </div>
</template>

<script setup lang="ts">
import ChatPanel from '@/components/chat/ChatPanel.vue'
</script>

<style scoped>
.agent-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
