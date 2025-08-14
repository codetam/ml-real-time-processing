<template>
  <v-app>
    <!-- Navbar with Tabs -->
    <v-app-bar app flat height="72" class="navbar-glass" elevation="1" color="rgba(0, 0, 0, 0.05)">
      <v-container class="d-flex align-center">
        <!-- Logo / Title -->
        <v-app-bar-title class="font-weight-bold text-h5 text-text">
          🚀 AI Vision Studio
        </v-app-bar-title>

        <v-spacer></v-spacer>

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
</style>