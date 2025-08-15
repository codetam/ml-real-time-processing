<template>
  <v-app>
    <div class="bg-overlay"></div>
    <!-- Navbar with Tabs -->
    <v-app-bar app flat height="72" class="navbar-glass" elevation="1" color="rgba(0, 0, 0, 0.05)">
      <v-container class="d-flex align-center">
        <!-- Logo / Title -->
        <v-app-bar-title class="font-weight-bold text-h5 text-text">
          🚀 AI Vision Studio
        </v-app-bar-title>

        <!-- Tabs -->
        <v-tabs
          v-model="activeTab"
          slider-color="primary"
          bg-color="transparent"
          class="text-text"
        >
          <v-tab v-for="tab in tabs" :key="tab">
            {{ tab }}
          </v-tab>
        </v-tabs>
      </v-container>
    </v-app-bar>

    <!-- Page Content -->
    <v-main>
      <v-container fluid>
        <component :is="currentComponent" />
      </v-container>
    </v-main>

    <!-- Footer -->
    <v-footer app class="navbar-glass text-black text-center">
      <v-col cols="12">
        © 2025 AI Vision Studio – Built with ❤️
      </v-col>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed } from "vue";
import ImageTester from './ImageTester.vue';
import VideoTester from './VideoTester.vue';


const tabs = ["Image Tester", "Video Tester"];
const activeTab = ref(0);

const currentComponent = computed(() => {
  return activeTab.value === 0 ? ImageTester : VideoTester;
});
</script>

<style scoped>
/* Gradient background */
.v-application {
  background: linear-gradient(145deg, #b3e5fc, #b39ddb);
}
/*
.bg-overlay {
  background: linear-gradient(-45deg, #0f0f1a, #1a1a40, #0a0a1f, #1a0033);
  background-size: 400% 400%;
  animation: gradientBG 12s ease infinite;
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 0;
}
@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
*/


.bg-overlay {
  position: absolute;
  top: -20px;
  left: -20px;
  width: calc(100% + 40px);
  height: calc(100% + 40px);
  background-image: url('/src/assets/background.jpg');
  background-size: cover;
  background-repeat: no-repeat;
  animation: moveBG 60s linear infinite;
  filter: blur(12px);
  z-index: 0;
}

@keyframes moveBG {
  0%   { background-position: 0% 0%; }
  20%  { background-position: 15% 25%; }
  40%  { background-position: 30% 10%; }
  60%  { background-position: 45% 30%; }
  80%  { background-position: 25% 45%; }
  100% { background-position: 0% 0%; }
}


</style>