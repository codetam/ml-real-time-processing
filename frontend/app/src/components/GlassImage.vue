<template>
    <v-card class="pa-4 h-100 preview-card hover-scale">
        <v-card-title class="info text-text">
            <v-icon left class="text-text">mdi-camera</v-icon>
                {{ title }}
            <v-spacer></v-spacer>
        </v-card-title>
        <div v-if="previewUrl" class="text-center py-6 d-flex justify-center">
            <img :src="previewUrl" alt="Uploaded Preview" class="responsive-img rounded-lg" />
        </div>
        <div v-else class="placeholder">
            <v-icon size="64" color="grey lighten-1">mdi-image-off</v-icon>
            <p class="text-subtitle-1 mt-2">
                {{ subtitle }}
            </p>
        </div>
    </v-card>
</template>

<script setup lang="ts">

const { previewUrl = undefined, title = '', subtitle = '' } = defineProps<{
  previewUrl?: string | undefined;
  title?: string;
  subtitle?: string;
}>();

</script>

<style scoped>
.hover-scale {
  transition: transform 0.2s;
}

.hover-scale:hover {
  transform: scale(1.02);
}

.preview-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.preview-card:hover {
  transform: scale(1.02);
}

.responsive-img {
  max-width: 100%;
  height: auto;
  display: block;
  max-height: 100%;
  object-fit: contain;
}

.placeholder {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
}
</style>