<template>
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
            <div v-else class="json-placeholder py-6">
                <v-icon size="64" color="grey lighten-1">mdi-code-json</v-icon>
                <p class="text-subtitle-1 mt-2">
                    No JSON data yet
                </p>
            </div>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">

const { jsonData = undefined } = defineProps<{
  jsonData?: JSON | undefined;
}>();

const copySuccess: Ref<boolean> = ref(false)

const formattedJson = computed<string>(() =>
  jsonData ? syntaxHighlight(JSON.stringify(jsonData, null, 2)) : ''
)

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
</script>

<style scoped>
.glass-card {
  background: rgba(20, 20, 30, 0.85);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(16px);
  color: white;
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

.json-placeholder {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
}
</style>