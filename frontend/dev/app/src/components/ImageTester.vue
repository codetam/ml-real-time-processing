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

    <!-- Glassmorphism Upload Card -->
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
              <v-card class="pa-4 h-100 preview-card hover-scale">
                <v-card-title class="info text-text">
                  <v-icon left class="text-text">mdi-camera</v-icon>
                  Uploaded Image
                  <v-spacer></v-spacer>
                </v-card-title>
                <div v-if="imageFile" class="text-center py-6 d-flex justify-center">
                  <img :src="previewUrl" alt="Uploaded Preview" class="responsive-img rounded-lg" />
                </div>
                <div v-else class="placeholder">
                  <v-icon size="64" color="grey lighten-1">mdi-image-off</v-icon>
                  <p class="text-subtitle-1 mt-2">
                    Upload an image to display
                  </p>
                </div>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 h-100 preview-card hover-scale">
                <v-card-title class="text-text">
                  <v-icon left class="mr-2">mdi-camera</v-icon>
                  Proccessed Image
                  <v-spacer></v-spacer>
                </v-card-title>
                <div v-if="bboxProcessedUrl" class="text-center py-6 d-flex justify-center">
                  <img :src="bboxProcessedUrl" alt="Processed Preview" class="responsive-img rounded-lg" />
                </div>
                <div v-else class="placeholder">
                  <v-icon size="64" color="grey lighten-1">mdi-image-off</v-icon>
                  <p class="text-subtitle-1 mt-2">
                    Click Run AI to process
                  </p>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <v-divider class="my-8"></v-divider>

          <!-- JSON -->
          <v-card class="pa-4 glass-card">
            <v-card-title class="info text-text">
              <v-row>
                <v-col>
                  <v-icon class="text-text">mdi-code-json</v-icon>
                  Response
                </v-col>
                <v-col class="text-right">
                  <v-btn size="x-small" v-if="jsonData" @click="copyJsonToClipboard" icon color="black"
                    :title="copySuccess ? 'Copied!' : 'Copy to clipboard'">
                    <v-icon>{{ copySuccess ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-title>
            <v-card-text class="pa-0">
              <div v-if="jsonData">
                <pre class="json-content pa-4"><code v-html="formattedJson"></code></pre>
              </div>
              <div v-else class="placeholder py-6">
                <v-icon size="64" color="grey lighten-1">mdi-code-json</v-icon>
                <p class="text-subtitle-1 mt-2">
                  No JSON data yet
                </p>
              </div>
            </v-card-text>
          </v-card>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from "vue";

const selectedModel = ref(null);
const models = ["YOLO11"];
const loading = ref(false);

import { computed } from "vue";

const sessionId = "test-id"

// Image upload
const maxSize = 5000000 // 5 MB
const imageFile = ref<File | undefined>(undefined);
const errorMessage = 'Total image size should be less than 5 MB!'

// JSON data
const jsonData = ref<any>(null)
const copySuccess: Ref<boolean> = ref(false)

// WebSocket connection
const messages = ref<string[]>([]);
const ws = new WebSocket(`ws://localhost:8000/stream/ws/${sessionId}`);
ws.onmessage = async (event) => {
  console.log('WebSocket message received:', event.data);
  try {
    const parsedData = JSON.parse(event.data);
    jsonData.value = parsedData;

    if (imageFile.value) {
      bboxProcessedUrl.value = await generateImageWithBBoxes(imageFile.value, parsedData["detections"]);
    }

  } catch (e) {
    jsonData.value = {
      message: event.data,
      timestamp: new Date().toISOString()
    };
  }
};

function syntaxHighlight(json: string): string {
  const esc = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  return esc.replace(
    /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(?:\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match: string) => {
      let cls = 'json-number'
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'json-key' : 'json-string'
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean'
      } else if (/null/.test(match)) {
        cls = 'json-null'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}

const formattedJson = computed<string>(() =>
  jsonData.value ? syntaxHighlight(JSON.stringify(jsonData.value, null, 2)) : ''
)

const previewUrl = computed(() =>
  imageFile.value ? URL.createObjectURL(imageFile.value) : undefined
)

watch(imageFile, () => {
  bboxProcessedUrl.value = null;
})

async function processImage() {
  if (!imageFile.value) {
    console.log("No file selected");
    return;
  }

  const formData = new FormData();
  formData.append("image", imageFile.value);
  try {
    const res = await fetch(`http://localhost:8000/stream/upload-image/${sessionId}`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      throw new Error('Network response not ok');
    }
    const data = await res.json();
    console.log("Upload successful", data);
  } catch (error) {
    console.log("Failed uploading file")
  }

}

async function copyJsonToClipboard() {
  try {
    await navigator.clipboard.writeText(formattedJson.value)
    copySuccess.value = true
    console.log('JSON copied to clipboard!')
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
  } catch (err) {
    console.log('Failed to copy to clipboard')
  }
}

interface Bbox {
  x_min: number,
  y_min: number,
  x_max: number,
  y_max: number
}
interface Detection {
  label: string,
  confidence: number,
  bbox: Bbox
}
const bboxProcessedUrl = ref<string | null>(null);
async function generateImageWithBBoxes(file: File, detections: Detection[]) {
  return new Promise<string>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return reject('No canvas context');

      // Draw original image
      ctx.drawImage(img, 0, 0);

      detections.forEach((detection) => {
        // Draw bounding box
        ctx.strokeStyle = 'limegreen';
        ctx.lineWidth = 4;
        ctx.strokeRect(detection.bbox.x_min,
          detection.bbox.y_min,
          detection.bbox.x_max - detection.bbox.x_min,
          detection.bbox.y_max - detection.bbox.y_min);

        // Draw label
        ctx.fillStyle = 'limegreen';
        ctx.font = '32px sans-serif';
        const label = detection.label;
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(detection.bbox.x_min, detection.bbox.y_min - 36, textWidth + 10, 36);

        ctx.fillStyle = 'white';
        ctx.fillText(label, detection.bbox.x_min + 5, detection.bbox.y_min - 8);
      });
      // Export new image as Data URL
      resolve(canvas.toDataURL('image/png'));
    }

    img.onerror = (err) => reject(err);
    img.src = URL.createObjectURL(file);
  });
}

</script>

<style scoped>
.hero-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.glass-card {
  background: rgba(20, 20, 30, 0.85);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(16px);
  color: white;
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

.placeholder-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.placeholder-image {
  border-radius: 12px;
  max-width: 100%;
  opacity: 0.8;
}

.placeholder {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
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

.json-content {
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  padding: 1rem;
}

/* IMPORTANT: use :deep() so scoped CSS applies to v-html content */
.json-content :deep(.json-key) {
  color: #9cdcfe;
}

.json-content :deep(.json-string) {
  color: #ce9178;
}

.json-content :deep(.json-number) {
  color: #b5cea8;
}

.json-content :deep(.json-boolean) {
  color: #569cd6;
}

.json-content :deep(.json-null) {
  color: #569cd6;
  font-style: italic;
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