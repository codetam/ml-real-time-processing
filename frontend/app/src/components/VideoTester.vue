<template>
  <div class="page">

    <!-- ── Page header ──────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Real-time Inference</h1>
        <p class="page-sub">Stream live video through WebRTC and detect objects using Triton Inference Server.</p>
      </div>
    </div>

    <!-- ── Controls bar ─────────────────────────────────────────── -->
    <div class="controls-bar">
      <v-select
        v-model="selectedModel"
        :items="models"
        label="Model"
        variant="outlined"
        density="compact"
        hide-details
        :disabled="running"
        style="max-width: 180px; flex-shrink: 0;"
      />
      <v-btn
        color="primary"
        variant="flat"
        :disabled="running"
        height="40"
        rounded="lg"
        min-width="96"
        @click="start"
      >
        <v-icon start size="16">mdi-play</v-icon>Start
      </v-btn>
      <v-btn
        color="error"
        variant="outlined"
        :disabled="!running"
        height="40"
        rounded="lg"
        min-width="96"
        @click="stop"
      >
        <v-icon start size="16">mdi-stop</v-icon>Stop
      </v-btn>
      <div class="status-badge" :class="statusClass">
        <span class="status-dot" />{{ status }}
      </div>
    </div>

    <!-- ── Main grid ─────────────────────────────────────────────── -->
    <div class="content-grid">

      <!-- Video -->
      <div class="video-col">
        <div class="video-wrap">
          <div v-if="!running" class="video-idle">
            <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M15 10l4.553-2.277A1 1 0 0121 8.723v6.554a1 1 0 01-1.447.894L15 14M4 8a2 2 0 012-2h9a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V8z"/>
            </svg>
            <p>Press <strong>Start</strong> to begin streaming</p>
          </div>
          <video ref="videoEl" autoplay muted playsinline class="video-el" :class="{ 'video-el--on': running }" />
          <canvas ref="canvasEl" class="canvas-overlay" />
          <span v-if="running && latestDetections.length" class="video-badge">
            {{ latestDetections.length }} {{ latestDetections.length === 1 ? 'object' : 'objects' }}
          </span>
        </div>
      </div>

      <!-- Sidebar -->
      <aside class="sidebar">

        <!-- Pipeline -->
        <div class="card">
          <p class="card-label">PIPELINE</p>
          <div class="pipeline">
            <div class="pnode" :class="{ 'pnode--on': running }">
              <div class="pnode-box">CAM</div>
              <span class="pnode-tag">Webcam</span>
            </div>
            <div class="pedge" :class="{ 'pedge--on': running }">
              <span class="pdot" style="animation-delay:0s"/>
              <span class="pdot" style="animation-delay:.55s"/>
              <span class="pdot" style="animation-delay:1.1s"/>
            </div>
            <div class="pnode" :class="{ 'pnode--on': running }">
              <div class="pnode-box">RTC</div>
              <span class="pnode-tag">WebRTC</span>
            </div>
            <div class="pedge" :class="{ 'pedge--on': running }">
              <span class="pdot" style="animation-delay:.18s"/>
              <span class="pdot" style="animation-delay:.73s"/>
              <span class="pdot" style="animation-delay:1.28s"/>
            </div>
            <div class="pnode" :class="{ 'pnode--on': running }">
              <div class="pnode-box">GPU</div>
              <span class="pnode-tag">Triton</span>
            </div>
            <div class="pedge" :class="{ 'pedge--on': running }">
              <span class="pdot" style="animation-delay:.36s"/>
              <span class="pdot" style="animation-delay:.91s"/>
              <span class="pdot" style="animation-delay:1.46s"/>
            </div>
            <div class="pnode" :class="{ 'pnode--on': running }">
              <div class="pnode-box">OUT</div>
              <span class="pnode-tag">Results</span>
            </div>
          </div>
        </div>

        <!-- Metrics -->
        <div class="card">
          <p class="card-label">METRICS</p>
          <div class="metrics">
            <div class="metric">
              <span class="metric-num">{{ running && inferenceMs > 0 ? inferenceMs.toFixed(1) : '—' }}</span>
              <span class="metric-unit">ms</span>
              <span class="metric-lbl">Inference</span>
            </div>
            <div class="metric-sep" />
            <div class="metric">
              <span class="metric-num">{{ running ? throughputFps : '—' }}</span>
              <span class="metric-unit">fps</span>
              <span class="metric-lbl">Throughput</span>
            </div>
            <div class="metric-sep" />
            <div class="metric">
              <span class="metric-num">{{ totalObjects }}</span>
              <span class="metric-unit" />
              <span class="metric-lbl">Total Det.</span>
            </div>
          </div>
        </div>

        <!-- Latency sparkline -->
        <div class="card">
          <div class="card-label-row">
            <p class="card-label">LATENCY</p>
            <span v-if="inferenceMs > 0" class="card-label-aside">{{ inferenceMs.toFixed(1) }} ms</span>
          </div>
          <canvas ref="chartEl" class="chart-canvas" />
        </div>

        <!-- Detections list -->
        <div class="card">
          <p class="card-label">DETECTIONS</p>
          <div v-if="latestDetections.length" class="det-list">
            <div v-for="(d, i) in latestDetections" :key="i" class="det-row">
              <span class="det-name">{{ d.label }}</span>
              <div class="det-bar-bg">
                <div class="det-bar-fg" :style="{ width: (parseFloat(d.confidence) * 100) + '%' }" />
              </div>
              <span class="det-score">{{ d.confidence }}</span>
            </div>
          </div>
          <p v-else class="det-empty">{{ running ? 'No objects in frame' : 'Waiting for stream…' }}</p>
        </div>

      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchJsonContent } from '@/utils/request'

interface Detection {
  label: string
  confidence: string
  bbox: { x_min: number; y_min: number; x_max: number; y_max: number }
}

const videoEl   = ref<HTMLVideoElement | null>(null)
const canvasEl  = ref<HTMLCanvasElement | null>(null)
const chartEl   = ref<HTMLCanvasElement | null>(null)

const selectedModel    = ref('')
const models           = ref<string[]>([])
const running          = ref(false)
const status           = ref('Idle')
const inferenceMs      = ref(0)
const latencyHistory   = ref<number[]>([])
const latestDetections = ref<Detection[]>([])
const totalObjects     = ref(0)
const throughputFps    = ref(0)

let pc:          RTCPeerConnection | null = null
let dataChannel: RTCDataChannel   | null = null
let localStream: MediaStream       | null = null

const _fpsWin: number[] = []
let   _fpsTick: ReturnType<typeof setInterval> | null = null

const statusClass = computed(() => ({
  'status-badge--idle':   status.value === 'Idle',
  'status-badge--warn':   ['Requesting webcam...', 'Connecting...'].includes(status.value),
  'status-badge--ok':     status.value === 'Connected',
  'status-badge--err':    status.value.startsWith('Error'),
}))

onMounted(async () => {
  await loadModels()
  _fpsTick = setInterval(() => {
    const now = Date.now()
    while (_fpsWin.length && now - _fpsWin[0] > 1000) _fpsWin.shift()
    throughputFps.value = _fpsWin.length
  }, 500)
})

onUnmounted(() => {
  if (_fpsTick) clearInterval(_fpsTick)
  stop()
})

async function loadModels() {
  const data = await fetchJsonContent('http://localhost:8000/models', { method: 'GET' })
  models.value = data.models
  if (models.value.length) selectedModel.value = models.value[0]
  console.log('[VideoTester] models:', models.value)
}

// ── WebRTC ─────────────────────────────────────────────────────────

async function start() {
  console.log('[WebRTC] start()')
  try {
    status.value = 'Requesting webcam...'
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    const track = localStream.getVideoTracks()[0]
    console.log('[WebRTC] webcam:', track.label, track.getSettings())

    if (videoEl.value) videoEl.value.srcObject = localStream
    status.value = 'Connecting...'

    const iceConfig: RTCConfiguration = {
      iceServers: [
        { urls: ['stun:turn.codetam.com:3478'] },
        { urls: ['turn:turn.codetam.com:3478'], username: 'user', credential: 'my_static_secret' },
      ],
    }
    console.log('[WebRTC] RTCPeerConnection', JSON.stringify(iceConfig))
    pc = new RTCPeerConnection(iceConfig)

    pc.onconnectionstatechange    = () => { console.log('[WebRTC] connection:', pc?.connectionState); onConnState() }
    pc.oniceconnectionstatechange = () => console.log('[WebRTC] ice-connection:', pc?.iceConnectionState)
    pc.onicegatheringstatechange  = () => console.log('[WebRTC] ice-gathering:', pc?.iceGatheringState)
    pc.onsignalingstatechange     = () => console.log('[WebRTC] signaling:', pc?.signalingState)
    pc.onicecandidate             = (e) => {
      if (e.candidate) console.log('[WebRTC] ICE candidate:', e.candidate.type, e.candidate.protocol, e.candidate.address)
      else             console.log('[WebRTC] ICE gathering complete')
    }

    for (const t of localStream.getTracks()) {
      pc.addTrack(t, localStream)
      console.log('[WebRTC] addTrack:', t.kind, t.label)
    }

    dataChannel = pc.createDataChannel('results', { ordered: true })
    console.log('[WebRTC] DataChannel created:', dataChannel.label)
    dataChannel.onopen    = () => console.log('[WebRTC] DataChannel open')
    dataChannel.onclose   = () => console.log('[WebRTC] DataChannel closed')
    dataChannel.onerror   = (e) => console.error('[WebRTC] DataChannel error:', e)
    dataChannel.onmessage = (e) => onDetection(e.data)

    console.log('[WebRTC] creating offer...')
    let offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    console.log('[WebRTC] offer SDP:\n', offer.sdp)

    await new Promise<void>((resolve) => {
      if (pc!.iceGatheringState === 'complete') { resolve(); return }
      pc!.addEventListener('icegatheringstatechange', () => { if (pc?.iceGatheringState === 'complete') resolve() })
    })

    offer = pc.localDescription!
    const sessionId = Math.random().toString(36).slice(2)
    const modelName = selectedModel.value || 'yolo11'
    console.log('[WebRTC] sending offer — session:', sessionId, 'model:', modelName)

    const resp = await fetch('http://localhost:8000/stream/webrtc/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sdp: offer.sdp, type: offer.type, session_id: sessionId, model_name: modelName }),
    })
    if (!resp.ok) throw new Error(`Server ${resp.status}: ${await resp.text()}`)

    const answer = await resp.json()
    console.log('[WebRTC] answer received:\n', answer.sdp)
    await pc.setRemoteDescription(answer)
    console.log('[WebRTC] remote desc set. signaling:', pc.signalingState)

  } catch (err: any) {
    console.error('[WebRTC] start() failed:', err)
    status.value = `Error: ${err.message}`
    running.value = false
  }
}

function onConnState() {
  const s = pc?.connectionState
  if (s === 'connected')                        { status.value = 'Connected'; running.value = true }
  if (s === 'failed' || s === 'disconnected')   { status.value = 'Disconnected'; running.value = false }
}

function onDetection(raw: string) {
  try {
    const msg = JSON.parse(raw) as { detections: Detection[]; inference_ms?: number }
    _fpsWin.push(Date.now())
    latestDetections.value = msg.detections
    totalObjects.value += msg.detections.length
    if (msg.inference_ms !== undefined) {
      inferenceMs.value = msg.inference_ms
      latencyHistory.value.push(msg.inference_ms)
      if (latencyHistory.value.length > 60) latencyHistory.value.shift()
      drawSparkline()
    }
    drawBoxes(msg.detections)
  } catch (e) { console.error('[VideoTester] parse error:', e) }
}

async function stop() {
  console.log('[WebRTC] stop()')
  pc?.close();          pc = null
  localStream?.getTracks().forEach((t) => t.stop()); localStream = null
  if (videoEl.value)  videoEl.value.srcObject = null
  if (canvasEl.value) canvasEl.value.getContext('2d')?.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  running.value = false; status.value = 'Idle'
  latestDetections.value = []; inferenceMs.value = 0
}

// ── Canvas: bounding boxes ──────────────────────────────────────

function drawBoxes(dets: Detection[]) {
  const canvas = canvasEl.value
  const video  = videoEl.value
  if (!canvas || !video || !video.videoWidth) return

  // Size canvas to match its CSS container (not the native video resolution)
  const W = canvas.offsetWidth
  const H = canvas.offsetHeight
  if (canvas.width !== W || canvas.height !== H) {
    canvas.width  = W
    canvas.height = H
  }

  // Compute the rendered region of the video inside the container.
  // The video uses object-fit:contain, so it may be letterboxed/pillarboxed.
  const videoAspect     = video.videoWidth / video.videoHeight
  const containerAspect = W / H
  let renderedW: number, renderedH: number
  if (videoAspect > containerAspect) {
    renderedW = W;               renderedH = W / videoAspect
  } else {
    renderedH = H;               renderedW = H * videoAspect
  }
  const offsetX = (W - renderedW) / 2
  const offsetY = (H - renderedH) / 2
  const scaleX  = renderedW / video.videoWidth
  const scaleY  = renderedH / video.videoHeight

  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, W, H)

  for (const d of dets) {
    // Map from native video coordinates to canvas display coordinates
    const x1 = offsetX + d.bbox.x_min * scaleX
    const y1 = offsetY + d.bbox.y_min * scaleY
    const x2 = offsetX + d.bbox.x_max * scaleX
    const y2 = offsetY + d.bbox.y_max * scaleY
    const bw = x2 - x1
    const bh = y2 - y1
    const cl = Math.max(8, Math.min(bw, bh) * 0.18)

    ctx.strokeStyle = 'rgba(0,82,255,0.6)'
    ctx.lineWidth = 1
    ctx.strokeRect(x1, y1, bw, bh)

    ctx.strokeStyle = '#0052ff'
    ctx.lineWidth = 2
    ctx.lineJoin = 'round'
    for (const [ox, oy, dx, dy] of [
      [x1, y1,  1,  1], [x2, y1, -1,  1],
      [x1, y2,  1, -1], [x2, y2, -1, -1],
    ] as [number, number, number, number][]) {
      ctx.beginPath()
      ctx.moveTo(ox + dx * cl, oy)
      ctx.lineTo(ox, oy)
      ctx.lineTo(ox, oy + dy * cl)
      ctx.stroke()
    }

    ctx.font = 'bold 11px Inter, -apple-system, sans-serif'
    const label = `${d.label} ${d.confidence}`
    const tw = ctx.measureText(label).width + 10
    const ly = y1 > 22 ? y1 - 22 : y1 + bh + 2
    ctx.fillStyle = '#0052ff'
    ctx.beginPath()
    ctx.roundRect(x1, ly, tw, 18, 3)
    ctx.fill()
    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x1 + 5, ly + 13)
  }
}

// ── Canvas: latency sparkline ───────────────────────────────────

function drawSparkline() {
  const canvas = chartEl.value
  if (!canvas) return
  const dpr  = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width  = rect.width  * dpr
  canvas.height = rect.height * dpr

  const ctx  = canvas.getContext('2d')!
  const data = latencyHistory.value
  if (data.length < 2) return

  const W   = canvas.width
  const H   = canvas.height
  const max = Math.max(...data) * 1.2 || 50
  const pt  = (i: number) => ({
    x: (i / (data.length - 1)) * W,
    y: H - (data[i] / max) * H * 0.88 - H * 0.06,
  })

  ctx.clearRect(0, 0, W, H)

  const grad = ctx.createLinearGradient(0, 0, 0, H)
  grad.addColorStop(0, 'rgba(0,82,255,0.15)')
  grad.addColorStop(1, 'rgba(0,82,255,0)')
  ctx.beginPath()
  for (let i = 0; i < data.length; i++) { const p = pt(i); i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y) }
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath()
  ctx.fillStyle = grad; ctx.fill()

  ctx.beginPath()
  for (let i = 0; i < data.length; i++) { const p = pt(i); i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y) }
  ctx.strokeStyle = '#0052ff'; ctx.lineWidth = 1.5 * dpr; ctx.lineJoin = 'round'; ctx.stroke()

  const last = pt(data.length - 1)
  ctx.beginPath(); ctx.arc(last.x, last.y, 2.5 * dpr, 0, Math.PI * 2)
  ctx.fillStyle = '#0052ff'; ctx.fill()
}
</script>

<style scoped>
/* ── Page ─────────────────────────────────────────────────────── */
.page { display: flex; flex-direction: column; gap: 24px; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title  { margin: 0; font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.02em; line-height: 1.2; }
.page-sub    { margin: 6px 0 0; font-size: 14px; color: #8a919e; line-height: 1.5; }

/* ── Controls bar ─────────────────────────────────────────────── */
.controls-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid transparent;
  transition: all 0.25s;
  margin-left: 4px;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

.status-badge--idle { color: #8a919e; border-color: rgba(138,145,158,0.25); background: rgba(138,145,158,0.06); }
.status-badge--warn { color: #f59e0b; border-color: rgba(245,158,11,0.25); background: rgba(245,158,11,0.06); }
.status-badge--ok   { color: #05b169; border-color: rgba(5,177,105,0.3);   background: rgba(5,177,105,0.08); }
.status-badge--ok .status-dot { animation: blink 2s ease-in-out infinite; }
.status-badge--err  { color: #f56565; border-color: rgba(245,101,101,0.3); background: rgba(245,101,101,0.08); }

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── Content grid ─────────────────────────────────────────────── */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 272px;
  gap: 16px;
  align-items: start;
}
@media (max-width: 880px) { .content-grid { grid-template-columns: 1fr; } }

/* ── Video ────────────────────────────────────────────────────── */
.video-col { min-width: 0; }

.video-wrap {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #0d0f14;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-idle {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #2d3139;
  pointer-events: none;
}
.video-idle svg { stroke: #2d3139; }
.video-idle p { font-size: 13px; margin: 0; color: #3a404c; }
.video-idle strong { color: #4b5260; font-weight: 600; }

.video-el { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; display: block; opacity: 0; transition: opacity 0.35s; }
.video-el--on { opacity: 1; }

.canvas-overlay { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.video-badge {
  position: absolute;
  top: 10px; left: 10px;
  padding: 3px 9px;
  background: rgba(10,11,13,0.8);
  border: 1px solid rgba(5,177,105,0.3);
  color: #05b169;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  border-radius: 4px;
  text-transform: uppercase;
}

/* ── Sidebar ──────────────────────────────────────────────────── */
.sidebar { display: flex; flex-direction: column; gap: 10px; }

.card {
  background: #111318;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 14px 16px;
}

.card-label {
  margin: 0 0 12px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #3a404c;
  text-transform: uppercase;
}
.card-label-row { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.card-label-row .card-label { margin: 0; }
.card-label-aside { font-size: 11px; font-weight: 600; color: #0052ff; font-variant-numeric: tabular-nums; }

/* ── Pipeline ─────────────────────────────────────────────────── */
.pipeline { display: flex; align-items: center; }

.pnode { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.pnode-box {
  width: 36px; height: 36px;
  border-radius: 7px;
  background: #0d0f14;
  border: 1px solid rgba(255,255,255,0.06);
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 800; letter-spacing: 0.05em;
  color: #3a404c;
  font-variant: all-small-caps;
  transition: border-color 0.3s, color 0.3s, box-shadow 0.3s;
}
.pnode--on .pnode-box {
  border-color: rgba(0,82,255,0.4);
  color: #6699ff;
  box-shadow: 0 0 12px rgba(0,82,255,0.1);
}
.pnode-tag { font-size: 8px; color: #2d3139; font-weight: 500; letter-spacing: 0.03em; transition: color 0.3s; }
.pnode--on .pnode-tag { color: #4b5260; }

.pedge { flex: 1; height: 36px; position: relative; overflow: hidden; }
.pedge::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: rgba(255,255,255,0.05); transition: background 0.3s; }
.pedge--on::before { background: rgba(0,82,255,0.18); }

.pdot { position: absolute; top: 50%; left: 0; width: 4px; height: 4px; border-radius: 50%; background: #0052ff; margin-top: -2px; opacity: 0; }
.pedge--on .pdot { animation: pdot-flow 1.65s linear infinite; }
@keyframes pdot-flow { 0%{left:-4px;opacity:0} 10%{opacity:1} 90%{opacity:1} 100%{left:100%;opacity:0} }

/* ── Metrics ──────────────────────────────────────────────────── */
.metrics { display: flex; align-items: center; }
.metric { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.metric-num { font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -0.03em; line-height: 1; font-variant-numeric: tabular-nums; }
.metric-unit { font-size: 9px; color: #4b5260; font-weight: 600; letter-spacing: 0.04em; margin-top: 1px; }
.metric-lbl  { font-size: 9px; color: #3a404c; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 3px; }
.metric-sep  { width: 1px; height: 30px; background: rgba(255,255,255,0.05); flex-shrink: 0; }

/* ── Latency chart ────────────────────────────────────────────── */
.chart-canvas { display: block; width: 100%; height: 68px; border-radius: 4px; }

/* ── Detections ───────────────────────────────────────────────── */
.det-list { display: flex; flex-direction: column; gap: 8px; }
.det-row  { display: grid; grid-template-columns: 72px 1fr 34px; align-items: center; gap: 8px; }
.det-name { font-size: 12px; color: #c8d0db; font-weight: 500; text-transform: capitalize; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.det-bar-bg { height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.det-bar-fg { height: 100%; background: #0052ff; border-radius: 2px; transition: width 0.2s ease; }
.det-score  { font-size: 10px; color: #4b5260; font-variant-numeric: tabular-nums; text-align: right; }
.det-empty  { margin: 0; font-size: 12px; color: #3a404c; text-align: center; padding: 8px 0; }
</style>
