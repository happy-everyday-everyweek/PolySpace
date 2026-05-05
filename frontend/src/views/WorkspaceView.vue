<template>
  <div class="workspace-page">
    <WorkspaceView />
  </div>
</template>

<script setup lang="ts">
import WorkspaceView from '@/components/workspace/WorkspaceView.vue'
</script>

<style scoped>
.workspace-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
