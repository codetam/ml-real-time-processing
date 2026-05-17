<template>
  <v-app>
    <div class="app-shell">

      <!-- ── Top navigation ───────────────────────────────────────── -->
      <header class="topnav">
        <div class="topnav-inner">
          <span class="logo">codetam<span class="logo-accent">/vision</span></span>
          <nav class="tabnav">
            <button
              v-for="(tab, i) in tabs"
              :key="tab"
              class="tabnav-item"
              :class="{ 'tabnav-item--active': activeTab === i }"
              @click="activeTab = i"
            >
              {{ tab }}
            </button>
          </nav>
        </div>
      </header>

      <!-- ── Page content ─────────────────────────────────────────── -->
      <main class="page-content">
        <component :is="currentComponent" />
      </main>

    </div>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import ImageTester from './ImageTester.vue'
import VideoTester from './VideoTester.vue'

const tabs = ['Image Tester', 'Video Tester']
const activeTab = ref(0)
const currentComponent = computed(() => activeTab.value === 0 ? ImageTester : VideoTester)
</script>

<style>
/* ── Global reset ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

.v-application {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  background: #0a0b0d !important;
  color: #ffffff !important;
}

/* Make Vuetify v-select look right in our dark context */
.v-field__outline { --v-field-border-opacity: 1 !important; }
</style>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #0a0b0d;
}

/* ── Top nav ──────────────────────────────────────────────────── */
.topnav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #0a0b0d;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  height: 56px;
  display: flex;
  align-items: center;
}

.topnav-inner {
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.02em;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}
.logo-accent {
  color: #0052ff;
  font-weight: 400;
}

.tabnav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tabnav-item {
  height: 56px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 500;
  color: #8a919e;
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  transition: color 0.15s;
  font-family: inherit;
}

.tabnav-item:hover { color: #c8d0db; }

.tabnav-item--active { color: #ffffff; }

.tabnav-item--active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 16px;
  right: 16px;
  height: 2px;
  background: #0052ff;
  border-radius: 2px 2px 0 0;
}

/* ── Page ─────────────────────────────────────────────────────── */
.page-content {
  flex: 1;
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 32px 24px;
}
</style>
