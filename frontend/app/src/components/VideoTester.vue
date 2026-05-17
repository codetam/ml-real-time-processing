<template>
  <v-container fluid class="pa-0 hero-container">
    <v-spacer style="height: 8rem;" />

    <v-row align="center" justify="center" class="mb-4 mt-10 z-top">
      <v-col cols="12" md="8" class="text-center">
        <p class="text-h2 font-weight-bold neon-text mb-4">Video Model Tester</p>
        <p class="text-h5 opacity-75">
          Stream your webcam and get real-time AI inference results.
        </p>
      </v-col>
    </v-row>

    <v-spacer style="height: 4rem;" />

    <v-row justify="center" class="z-top">
      <v-col cols="12" md="10" lg="8">

        <!-- Controls -->
        <v-row align="center" justify="center" dense class="mb-6">
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedModel"
              :items="models"
              label="Select Model"
              prepend-icon="mdi-robot"
              variant="outlined"
              density="comfortable"
              class="hover-scale"
            />
          </v-col>
          <v-col cols="auto" class="mx-2">
            <v-btn class="modern-run-btn" size="large" @click="start" :disabled="running">
              <v-icon start>mdi-play</v-icon>
              Start
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn class="modern-stop-btn" size="large" @click="stop" :disabled="!running">
              <v-icon start>mdi-stop</v-icon>
              Stop
            </v-btn>
          </v-col>
        </v-row>

        <!-- Connection status -->
        <v-row justify="center" class="mb-6">
          <v-chip :color="statusColor" label size="large">{{ status }}</v-chip>
        </v-row>

        <!-- Video + bounding-box canvas overlay -->
        <v-row justify="center" class="mb-8">
          <v-col cols="12">
            <div class="video-wrapper">
              <video ref="videoEl" autoplay muted playsinline class="webcam-video" />
              <canvas ref="canvasEl" class="overlay-canvas" />
            </div>
          </v-col>
        </v-row>

        <v-divider class="my-8" />

        <JsonDataContainer :json-data="lastResult" />

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchJsonContent } from '@/utils/request'
import JsonDataContainer from './JsonDataContainer.vue'

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const selectedModel = ref<string | null>(null)
const models = ref<string[]>([])
const running = ref(false)
const status = ref('Idle')
const lastResult = ref<object | undefined>(undefined)

let pc: RTCPeerConnection | null = null
let dataChannel: RTCDataChannel | null = null
let localStream: MediaStream | null = null

const statusColor = computed(() => {
  if (status.value === 'Connected') return 'success'
  if (status.value === 'Idle') return 'default'
  if (status.value.startsWith('Error')) return 'error'
  return 'warning'
})

onMounted(async () => {
  await loadModels()
})

onUnmounted(() => {
  stop()
})

async function loadModels() {
  const data = await fetchJsonContent('http://localhost:8000/models', { method: 'GET' })
  models.value = data.models
  if (models.value.length > 0) selectedModel.value = models.value[0]
  console.log('[WebRTC] Available models:', models.value)
}

async function start() {
  console.log('[WebRTC] Starting connection...')
  try {
    status.value = 'Requesting webcam...'
    console.log('[WebRTC] Requesting getUserMedia...')
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    const videoTrack = localStream.getVideoTracks()[0]
    console.log('[WebRTC] Got stream. Video track:', videoTrack.label, videoTrack.getSettings())

    if (videoEl.value) videoEl.value.srcObject = localStream

    status.value = 'Connecting...'

    const iceConfig: RTCConfiguration = {
      iceServers: [
        { urls: ['stun:turn.codetam.com:3478'] },
        { urls: ['turn:turn.codetam.com:3478'], username: 'user', credential: 'my_static_secret' }
      ]
    }
    console.log('[WebRTC] Creating RTCPeerConnection with config:', JSON.stringify(iceConfig))
    pc = new RTCPeerConnection(iceConfig)

    pc.onconnectionstatechange = () => {
      console.log('[WebRTC] Connection state:', pc?.connectionState)
      if (pc?.connectionState === 'connected') {
        status.value = 'Connected'
        running.value = true
      } else if (pc?.connectionState === 'failed' || pc?.connectionState === 'disconnected') {
        status.value = 'Disconnected'
        running.value = false
      }
    }

    pc.oniceconnectionstatechange = () => {
      console.log('[WebRTC] ICE connection state:', pc?.iceConnectionState)
    }

    pc.onicegatheringstatechange = () => {
      console.log('[WebRTC] ICE gathering state:', pc?.iceGatheringState)
    }

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        console.log('[WebRTC] ICE candidate:', event.candidate.type, event.candidate.address, event.candidate.protocol)
      } else {
        console.log('[WebRTC] ICE gathering complete (null candidate)')
      }
    }

    pc.onsignalingstatechange = () => {
      console.log('[WebRTC] Signaling state:', pc?.signalingState)
    }

    // Add webcam video track so the server receives frames for inference
    for (const track of localStream.getTracks()) {
      const sender = pc.addTrack(track, localStream)
      console.log('[WebRTC] Added track to PC:', track.kind, track.label, 'sender:', sender)
    }

    // DataChannel for receiving inference results (server → client)
    dataChannel = pc.createDataChannel('results', { ordered: true })
    console.log('[WebRTC] DataChannel created:', dataChannel.label, 'id:', dataChannel.id)

    dataChannel.onopen = () => {
      console.log('[WebRTC] DataChannel open (readyState:', dataChannel?.readyState, ')')
    }
    dataChannel.onclose = () => {
      console.log('[WebRTC] DataChannel closed')
    }
    dataChannel.onerror = (e) => {
      console.error('[WebRTC] DataChannel error:', e)
    }
    dataChannel.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        lastResult.value = data
        drawDetections(data.detections ?? [])
      } catch (e) {
        console.error('[WebRTC] Failed to parse detection message:', e, event.data)
      }
    }

    // Create offer (SDP includes the video track and DataChannel)
    console.log('[WebRTC] Creating offer...')
    let offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    console.log('[WebRTC] Local description set. Offer type:', offer.type)
    console.log('[WebRTC] Offer SDP:\n', offer.sdp)

    // Wait for all ICE candidates before sending the offer
    await new Promise<void>((resolve) => {
      if (pc!.iceGatheringState === 'complete') {
        console.log('[WebRTC] ICE already complete')
        resolve()
      } else {
        pc!.addEventListener('icegatheringstatechange', () => {
          if (pc?.iceGatheringState === 'complete') {
            console.log('[WebRTC] ICE gathering finished')
            resolve()
          }
        })
      }
    })

    offer = pc.localDescription!
    const sessionId = Math.random().toString(36).slice(2)
    const modelName = selectedModel.value ?? 'yolo11'

    const body = {
      sdp: offer.sdp,
      type: offer.type,
      session_id: sessionId,
      model_name: modelName
    }
    console.log('[WebRTC] Sending offer to server. session_id:', sessionId, 'model:', modelName)

    const resp = await fetch('http://localhost:8000/stream/webrtc/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!resp.ok) throw new Error(`Server returned ${resp.status}: ${await resp.text()}`)

    const answer = await resp.json()
    console.log('[WebRTC] Answer received from server. type:', answer.type)
    console.log('[WebRTC] Answer SDP:\n', answer.sdp)

    await pc.setRemoteDescription(answer)
    console.log('[WebRTC] Remote description set. Signaling state:', pc.signalingState)

  } catch (e: any) {
    console.error('[WebRTC] Error during start:', e)
    status.value = `Error: ${e.message}`
    running.value = false
  }
}

function drawDetections(detections: any[]) {
  const canvas = canvasEl.value
  const video = videoEl.value
  if (!canvas || !video || !video.videoWidth) return

  // Sync canvas internal resolution to native video resolution (only when it changes)
  if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    console.log('[Canvas] Resized to', canvas.width, 'x', canvas.height)
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  for (const det of detections) {
    const { x_min, y_min, x_max, y_max } = det.bbox
    const w = x_max - x_min
    const h = y_max - y_min
    const label = `${det.label}: ${parseFloat(det.confidence).toFixed(2)}`

    ctx.strokeStyle = 'lime'
    ctx.lineWidth = 2
    ctx.strokeRect(x_min, y_min, w, h)

    const textWidth = ctx.measureText(label).width + 8
    ctx.fillStyle = 'rgba(0,0,0,0.7)'
    ctx.fillRect(x_min, y_min - 22, textWidth, 22)
    ctx.fillStyle = 'lime'
    ctx.font = 'bold 14px monospace'
    ctx.fillText(label, x_min + 4, y_min - 6)
  }
}

async function stop() {
  console.log('[WebRTC] Stopping connection...')
  if (pc) {
    await pc.close()
    pc = null
  }
  if (localStream) {
    localStream.getTracks().forEach((t) => t.stop())
    localStream = null
  }
  if (videoEl.value) videoEl.value.srcObject = null
  if (canvasEl.value) {
    const ctx = canvasEl.value.getContext('2d')
    ctx?.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  }
  running.value = false
  status.value = 'Idle'
  lastResult.value = undefined
  console.log('[WebRTC] Stopped')
}
</script>

<style scoped>
.hero-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* Grows to the natural height of the <video> element (height: auto preserves aspect ratio) */
.video-wrapper {
  position: relative;
  width: 100%;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 16px;
  overflow: hidden;
}

.webcam-video {
  width: 100%;
  height: auto;
  display: block;
}

/*
 * Canvas is sized via JS to match the native video resolution (videoWidth × videoHeight).
 * CSS stretches it to cover exactly the same area as the video element.
 * Because both scale proportionally from the same source resolution, bbox coordinates are always correct.
 */
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.z-top {
  position: relative;
  z-index: 1;
}

.neon-text {
  color: #f5f5f7;
  text-shadow: 0 0 8px rgba(0, 255, 255, 0.7);
}

.hover-scale {
  transition: transform 0.2s;
}

.hover-scale:hover {
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
}

.modern-run-btn:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 18px rgba(142, 45, 226, 0.6);
}

.modern-stop-btn {
  background: radial-gradient(circle at center, #e22d2d, #9b0000);
  color: white !important;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 4px 12px rgba(226, 45, 45, 0.4);
  text-transform: none !important;
}

.modern-stop-btn:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 18px rgba(226, 45, 45, 0.6);
}
</style>
