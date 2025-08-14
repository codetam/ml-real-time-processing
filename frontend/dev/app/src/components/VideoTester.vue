<template>
  <v-container class="py-8">
    <v-card elevation="3" class="pa-6 rounded-xl">
      <v-row align="center" class="mb-6">
        <v-col>
          <h1 class="text-h4 font-weight-bold text-primary">🎥 Video Model Tester</h1>
          <p class="text-subtitle-1 text-grey-darken-1">
            Stream or upload a video, choose your AI model, and watch live detections.
          </p>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12" md="4">
          <v-file-input
            v-model="videoFile"
            label="Upload Video"
            prepend-icon="mdi-video"
            accept="video/*"
            variant="outlined"
            density="comfortable"
          />
        </v-col>

        <v-col cols="12" md="4">
          <v-select
            v-model="selectedModel"
            :items="models"
            label="Select Model"
            prepend-icon="mdi-robot"
            variant="outlined"
            density="comfortable"
          />
        </v-col>

        <v-col cols="12" md="2">
          <v-text-field
            v-model="frequency"
            label="Update Frequency (s)"
            type="number"
            min="0.1"
            step="0.1"
            prepend-icon="mdi-timer"
            variant="outlined"
            density="comfortable"
          />
        </v-col>

        <v-col cols="12" md="2" class="d-flex align-center">
          <v-btn
            color="primary"
            class="w-100"
            size="large"
            @click="startVideoProcessing"
            :disabled="!videoFile || !selectedModel"
          >
            Start
          </v-btn>
        </v-col>
      </v-row>

      <v-divider class="my-6"></v-divider>

      <v-row v-if="results">
        <v-col cols="12" md="6">
          <v-card class="pa-4" outlined>
            <h3 class="text-h6 font-weight-bold">📜 JSON Results</h3>
            <pre class="mt-3 bg-grey-lighten-3 pa-3 rounded">{{ results }}</pre>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="pa-4" outlined>
            <h3 class="text-h6 font-weight-bold">📹 Processed Video</h3>
            <div
              class="mt-3 d-flex align-center justify-center bg-grey-lighten-3 rounded"
              style="height:300px;"
            >
              Bounding box overlay placeholder
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from "vue";

const videoFile = ref(null);
const selectedModel = ref(null);
const frequency = ref(1);
const models = ["YOLOv11", "YOLOv8", "Custom Model"];
const results = ref(null);

function startVideoProcessing() {
  results.value = JSON.stringify(
    { detections: [{ frame: 1, label: "person", confidence: 0.88 }] },
    null,
    2
  );
}
</script>
