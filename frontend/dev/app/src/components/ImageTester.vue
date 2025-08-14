<template>
  <v-container fluid class="px-8 py-12 text-text">
    <!-- Hero -->
    <v-row align="center" justify="center" class="mb-4">
      <v-col cols="12" md="8" class="text-center">
        <h2 class="text-h3 font-weight-bold mb-4">Image Model Tester</h2>
        <p class="text-subtitle-1 opacity-75">
          Upload an image, choose an AI model, and preview beautiful detection results.
        </p>
      </v-col>
    </v-row>

    <!-- Glassmorphism Upload Card -->
    <v-row justify="center">
      <v-col cols="12" md="10">
        <v-card variant="text" class="pa-6" elevation="0">
          <v-row class="px-10">
            <v-col cols="12" md="1"></v-col>
            <v-col cols="12" md="4">
              <v-file-input v-model="imageFile" label="Upload Image" prepend-icon="mdi-image" accept="image/*"
                variant="outlined" density="comfortable" class="hover-scale"/>
            </v-col>

            <v-col cols="12" md="4">
              <v-select v-model="selectedModel" :items="models" label="Select Model" prepend-icon="mdi-robot"
                variant="outlined" density="comfortable" class="hover-scale" />
            </v-col>

            <v-col cols="12" md="2" class="h-100">
              <v-btn color="pink-darken-3" class="w-100 hover-scale" size="large" @click="processImage"
                :disabled="!imageFile">
                <v-progress-circular v-if="loading" indeterminate size="20" color="black" class="mr-2" />
                {{ loading ? 'Processing...' : 'Process' }}
              </v-btn>
            </v-col>
            <v-col cols="12" md="1"></v-col>
          </v-row>

          <v-divider class="my-6"></v-divider>

          <!-- Images -->
          <v-row style="min-height: 400px;">
            <v-col cols="12" md="6">
              <v-card class="pa-4 h-100">
                <v-card-title class="info black--text">
                  <v-icon left class="text-text">mdi-camera</v-icon>
                  Uploaded Image
                  <v-spacer></v-spacer>
                </v-card-title>
                <div v-if="imageFile" class="text-center py-8 d-flex justify-center">
                  <img :src="previewUrl" alt="Uploaded Preview" class="responsive-img rounded-lg" />
                </div>
                <div v-else class="text-center pb-8 h-100 d-flex flex-column justify-center align-center">
                  <v-icon size="64" color="grey lighten-1">mdi-image-off</v-icon>
                  <p class="text-subtitle-1 text-text mt-2">
                    Upload an image to display
                  </p>
                </div>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card class="pa-4 h-100">
                <v-card-title class="info black--text">
                  <v-icon left class="text-text">mdi-camera</v-icon>
                  Proccessed Image
                  <v-spacer></v-spacer>
                </v-card-title>
                <div v-if="bboxProcessedUrl" class="text-center py-8 d-flex justify-center">
                  <img :src="bboxProcessedUrl" alt="Processed Preview" class="responsive-img rounded-lg" />
                </div>
                <div v-else class="text-center pb-8 h-100 d-flex flex-column justify-center align-center">
                  <v-icon size="64" color="grey lighten-1">mdi-image-off</v-icon>
                  <p class="text-subtitle-1 text-text mt-2">
                    Click on Process to display
                  </p>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <v-divider class="my-6"></v-divider>

          <!-- JSON -->
          <v-row>
            <v-card class="pa-4 glass-card">
              <v-card-title class="info black--text">
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
                <div v-if="jsonData" class="json-container">
                  <pre class="json-content pa-4"><code>{{ formattedJson }}</code></pre>
                </div>
                <div v-else class="text-center py-8 pa-4">
                  <v-icon size="64" color="grey lighten-1">mdi-code-json</v-icon>
                  <p class="text-subtitle-1 grey--text mt-2">
                    No JSON data to display
                  </p>
                </div>
              </v-card-text>
            </v-card>
          </v-row>
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

const sessionId = "test-session-id"

// Image upload
const maxSize = 5000000 // 5 MB
const imageFile = ref<File | null>(null);
const errorMessage = 'Total image size should be less than 5 MB!'
const rules: ((value: File | null) => boolean | string)[] = [
  (value) => {
    if (!value) return true;
    return value.size <= maxSize || errorMessage;
  },
];

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

const formattedJson = computed(() => {
  return jsonData.value ? JSON.stringify(jsonData.value, null, 2) : ''
});

const previewUrl = computed(() =>
  imageFile.value ? URL.createObjectURL(imageFile.value) : undefined
)

watch( imageFile, () => {
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
.glass-card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.hover-scale {
  transition: transform 0.2s ease;
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
</style>