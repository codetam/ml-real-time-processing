<template>
  <v-container fluid class="pa-0 hero-container">
    <v-spacer style="height: 8rem;"></v-spacer>
    <!-- Hero -->
    <v-row align="center" justify="center" class="mb-4 mt-10 z-top">
      <v-col cols="12" md="8" class="text-center">
        <p class="text-h2 font-weight-bold neon-text mb-4">Image Model Tester</p>
        <p class="text-h5 opacity-75">
          Upload an image, choose an AI model, and preview beautiful detection results.
        </p>
      </v-col>
    </v-row>

    <v-spacer style="height: 8rem;"></v-spacer>

    <v-row justify="center" class="z-top">
      <v-col cols="12" md="10" lg="10">
        <v-card variant="text" class="pa-6" elevation="0">
          <v-row align="center" justify="center" dense>
            <v-col cols="12" md="5">
              <div class="upload-image hover-scale">
                <v-file-upload class="text-text" v-model="imageFile" title="Upload your image" accept="image/*"
                  width="100%" density="compact"
                  style="background: transparent !important; box-shadow: none !important;" />
              </div>
            </v-col>
            <v-col md="1"></v-col>
            <v-col cols="12" md="4" class="">
              <v-row class="w-100">
                <v-select v-model="selectedModel" :items="models" label="Select Model" prepend-icon="mdi-robot"
                  variant="outlined" density="comfortable" class="hover-scale" />
              </v-row>
              <v-divider class="my-8"></v-divider>
              <v-row class="w-100">
                <v-btn class="modern-run-btn w-100" size="large" @click="processImage" :disabled="!imageFile">
                  <v-progress-circular v-if="loading" indeterminate size="20" color="white" class="mr-2" />
                  Run
                </v-btn>
              </v-row>
            </v-col>
            <v-col cols="12" md="1"></v-col>
          </v-row>

          <v-spacer style="height: 8rem;"></v-spacer>
          <v-divider class="my-1"></v-divider>
          <v-spacer style="height: 8rem;"></v-spacer>

          <!-- Images -->
          <v-row style="min-height: 400px;">
            <v-col cols="12" md="6">
              <GlassImage title="Uploaded Image" subtitle="Upload an image to display" :preview-url="previewUrl" />
            </v-col>
            <v-col cols="12" md="6">
              <GlassImage title="Proccessed Image" subtitle="Click Run AI to process" :preview-url="bboxProcessedUrl" />
            </v-col>
          </v-row>

          <v-divider class="my-8"></v-divider>

          <JsonDataContainer :json-data="jsonData" />

        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { fetchJsonContent } from "@/utils/request";
import { generateImageWithBBoxes } from "@/utils/yolo";
import { ref } from "vue";
import { computed } from "vue";

const imageFile = ref<File | undefined>(undefined);
const bboxProcessedUrl = ref<string | undefined>(undefined);
const jsonData = ref<JSON | undefined>(undefined);

let sessionId: string | undefined = undefined;
let ws: WebSocket | undefined = undefined;

const selectedModel = ref(null);
const models: Ref<string[]> = ref([])
const loading = ref(false);

onMounted( async () => {
  loadModels();
})

async function loadModels() {
  const data = await fetchJsonContent(`http://localhost:8000/models`, {
    method: 'GET'
  });
  models.value = data.models;
}

async function fetchSessionId() {
  const data = await fetchJsonContent(`http://localhost:8000/session`, {
    method: 'POST'
  });
  sessionId = data.session_id;
}

async function startWebsocketConnection() {
  if (!sessionId) {
    await fetchSessionId();
  }

  const ws = new WebSocket(`ws://localhost:8000/results/ws/${sessionId}`);
  ws.onmessage = async (event) => {
    console.log('WebSocket message received:', event.data);
    try {
      const parsedData = JSON.parse(event.data);
      jsonData.value = parsedData;

      if (imageFile.value) {
        bboxProcessedUrl.value = await generateImageWithBBoxes(imageFile.value, parsedData["detections"]);
      }

    } catch (e) {
      console.log('Error while parsing JSON message');
    }
  };
}

const previewUrl = computed(() =>
  imageFile.value ? URL.createObjectURL(imageFile.value) : undefined
)

watch(imageFile, () => {
  bboxProcessedUrl.value = undefined;
})

async function processImage() {
  if (!imageFile.value) {
    console.log("No file selected");
    return;
  }

  if (!ws) {
    await startWebsocketConnection();
  }

  const formData = new FormData();
  formData.append("image", imageFile.value);
  await fetchJsonContent(`http://localhost:8000/image/test/${selectedModel.value}/${sessionId}`, {
    method: 'POST',
    body: formData
  });
}
</script>

<style scoped>
.hero-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.upload-image {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  backdrop-filter: blur(16px);
  color: white;
}

.hover-scale {
  transition: transform 0.2s;
}

.hover-scale:hover {
  transform: scale(1.02);
}

.responsive-img {
  max-width: 100%;
  height: auto;
  display: block;
  max-height: 100%;
  object-fit: contain;
}

.relative-container {
  position: relative;
  /* important: makes the canvas align with the image */
  display: inline-block;
  /* keeps it tight to the image */
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  /* let clicks pass through */
}

.z-top {
  position: relative;
  z-index: 1;
}

.neon-text {
  color: #F5F5F7;
  text-shadow: 0 0 8px rgba(0, 255, 255, 0.7);
}

.preview-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.preview-card:hover {
  transform: scale(1.02);
}

.modern-run-btn {
  background: radial-gradient(circle at center, #8e2de2, #4a00e0);
  color: white !important;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 4px 12px rgba(142, 45, 226, 0.4);
  text-transform: none !important;
  /* <-- stops uppercase */
}

.modern-run-btn:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 18px rgba(142, 45, 226, 0.6);
}

.modern-run-btn:disabled {
  background: radial-gradient(circle at center, #999, #777);
  color: rgba(255, 255, 255, 0.6) !important;
  box-shadow: none;
  transform: none;
}

.file-upload {
  color: rgba(142, 45, 226, 0.6) ! important;
}
</style>