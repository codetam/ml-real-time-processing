<template>
  <div class="page">

    <!-- ── Page header ──────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Image Inference</h1>
        <p class="page-sub">Upload an image, select a model, and run object detection.</p>
      </div>
    </div>

    <!-- ── Main grid ─────────────────────────────────────────────── -->
    <div class="content-grid">

      <!-- Left: upload + controls -->
      <div class="left-col">

        <!-- Dropzone -->
        <div
          class="dropzone"
          :class="{ 'dropzone--active': isDragging, 'dropzone--filled': !!imageFile }"
          @click="fileInputEl?.click()"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <input ref="fileInputEl" type="file" accept="image/*" style="display:none" @change="onFileChange" />

          <template v-if="!imageFile">
            <svg class="dz-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
            </svg>
            <p class="dz-text">Drop image here or <span class="dz-link">browse</span></p>
            <p class="dz-hint">PNG, JPG, WEBP</p>
          </template>

          <template v-else>
            <img :src="previewUrl" class="dz-preview" />
            <div class="dz-change-hint">Click to change</div>
          </template>
        </div>

        <!-- Model + Run -->
        <div class="run-row">
          <v-select
            v-model="selectedModel"
            :items="models"
            label="Model"
            variant="outlined"
            density="compact"
            hide-details
            style="flex: 1;"
          />
          <v-btn
            color="primary"
            variant="flat"
            :disabled="!imageFile || loading"
            height="40"
            rounded="lg"
            min-width="100"
            @click="processImage"
          >
            <v-progress-circular v-if="loading" indeterminate size="16" width="2" color="white" class="mr-2" />
            <v-icon v-else start size="16">mdi-play</v-icon>
            Run
          </v-btn>
        </div>

      </div>

      <!-- Right: results -->
      <div class="right-col">

        <!-- Original image -->
        <div class="img-card">
          <p class="img-card-label">ORIGINAL</p>
          <div class="img-frame">
            <div v-if="!imageFile" class="img-placeholder">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
                <path d="M21 15l-5-5L5 21"/>
              </svg>
              <span>No image</span>
            </div>
            <img v-else :src="previewUrl" class="img-el" />
          </div>
        </div>

        <!-- Processed image -->
        <div class="img-card">
          <p class="img-card-label">DETECTIONS</p>
          <div class="img-frame">
            <div v-if="!bboxProcessedUrl" class="img-placeholder">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0 0h18"/>
              </svg>
              <span>Run to see results</span>
            </div>
            <img v-else :src="bboxProcessedUrl" class="img-el" />
          </div>
        </div>

      </div>
    </div>

    <!-- ── JSON output ───────────────────────────────────────────── -->
    <div v-if="jsonData" class="json-section">
      <div class="json-header">
        <p class="json-label">RESPONSE</p>
        <button class="json-copy" @click="copyJson">
          <v-icon size="14">mdi-content-copy</v-icon>
          {{ copied ? 'Copied' : 'Copy' }}
        </button>
      </div>
      <pre class="json-body"><code>{{ JSON.stringify(jsonData, null, 2) }}</code></pre>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchJsonContent } from '@/utils/request'
import { generateImageWithBBoxes } from '@/utils/yolo'

const fileInputEl      = ref<HTMLInputElement | null>(null)
const imageFile        = ref<File | undefined>(undefined)
const bboxProcessedUrl = ref<string | undefined>(undefined)
const jsonData         = ref<object | undefined>(undefined)
const selectedModel    = ref<string | null>(null)
const models           = ref<string[]>([])
const loading          = ref(false)
const isDragging       = ref(false)
const copied           = ref(false)

let sessionId: string | undefined = undefined
let ws:        WebSocket | undefined = undefined

const previewUrl = computed(() =>
  imageFile.value ? URL.createObjectURL(imageFile.value) : undefined
)

onMounted(async () => {
  const data = await fetchJsonContent('http://localhost:8000/models', { method: 'GET' })
  models.value = data.models
  if (models.value.length) selectedModel.value = models.value[0]
})

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) setFile(file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) setFile(file)
}

function setFile(file: File) {
  imageFile.value = file
  bboxProcessedUrl.value = undefined
  jsonData.value = undefined
}

async function processImage() {
  if (!imageFile.value) return
  loading.value = true

  try {
    if (!sessionId) {
      const s = await fetchJsonContent('http://localhost:8000/session', { method: 'POST' })
      sessionId = s.session_id
    }

    if (!ws || ws.readyState !== WebSocket.OPEN) {
      ws = new WebSocket(`ws://localhost:8000/results/ws/${sessionId}`)
      ws.onmessage = async (event) => {
        try {
          const parsed = JSON.parse(event.data)
          jsonData.value = parsed
          if (imageFile.value) {
            bboxProcessedUrl.value = await generateImageWithBBoxes(imageFile.value, parsed.detections)
          }
        } catch {}
        loading.value = false
      }
      await new Promise<void>((resolve) => { ws!.onopen = () => resolve() })
    }

    const form = new FormData()
    form.append('image', imageFile.value)
    await fetchJsonContent(`http://localhost:8000/image/test/${selectedModel.value}/${sessionId}`, {
      method: 'POST',
      body: form,
    })
  } catch (e) {
    console.error('processImage error:', e)
    loading.value = false
  }
}

async function copyJson() {
  if (!jsonData.value) return
  await navigator.clipboard.writeText(JSON.stringify(jsonData.value, null, 2))
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
/* ── Page ─────────────────────────────────────────────────────── */
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { }
.page-title  { margin: 0; font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.02em; line-height: 1.2; }
.page-sub    { margin: 6px 0 0; font-size: 14px; color: #8a919e; }

/* ── Content grid ─────────────────────────────────────────────── */
.content-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  align-items: start;
}
@media (max-width: 800px) { .content-grid { grid-template-columns: 1fr; } }

/* ── Left col ─────────────────────────────────────────────────── */
.left-col { display: flex; flex-direction: column; gap: 10px; }

/* ── Dropzone ─────────────────────────────────────────────────── */
.dropzone {
  position: relative;
  background: #111318;
  border: 1.5px dashed rgba(255,255,255,0.1);
  border-radius: 10px;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  padding: 24px 16px;
  overflow: hidden;
}
.dropzone:hover       { border-color: rgba(0,82,255,0.4); background: rgba(0,82,255,0.03); }
.dropzone--active     { border-color: #0052ff; background: rgba(0,82,255,0.06); }
.dropzone--filled     { border-style: solid; border-color: rgba(255,255,255,0.08); padding: 0; }

.dz-icon  { width: 32px; height: 32px; stroke: #4b5260; }
.dz-text  { margin: 0; font-size: 13px; color: #8a919e; }
.dz-link  { color: #0052ff; font-weight: 500; }
.dz-hint  { margin: 0; font-size: 11px; color: #4b5260; }

.dz-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 8px;
  min-height: 180px;
  max-height: 260px;
}
.dz-change-hint {
  position: absolute;
  inset: 0;
  background: rgba(10,11,13,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #c8d0db;
  font-weight: 500;
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 8px;
}
.dropzone--filled:hover .dz-change-hint { opacity: 1; }

/* ── Run row ──────────────────────────────────────────────────── */
.run-row { display: flex; gap: 10px; align-items: center; }

/* ── Right col ────────────────────────────────────────────────── */
.right-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 560px) { .right-col { grid-template-columns: 1fr; } }

.img-card {
  background: #111318;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.img-card-label {
  margin: 0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #3a404c;
  text-transform: uppercase;
}
.img-frame {
  flex: 1;
  background: #0d0f14;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
}
.img-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #2d3139;
}
.img-placeholder svg { stroke: #2d3139; }
.img-placeholder span { font-size: 12px; color: #3a404c; }
.img-el { width: 100%; height: auto; display: block; }

/* ── JSON section ─────────────────────────────────────────────── */
.json-section {
  background: #111318;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  overflow: hidden;
}
.json-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.json-label {
  margin: 0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #3a404c;
  text-transform: uppercase;
}
.json-copy {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 500;
  color: #4b5260;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s;
}
.json-copy:hover { color: #8a919e; }
.json-body {
  margin: 0;
  padding: 16px;
  font-size: 12px;
  line-height: 1.6;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  color: #8a919e;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre;
}
.json-body code { color: inherit; }
</style>
