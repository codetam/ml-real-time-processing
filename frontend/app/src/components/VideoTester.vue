<template>
  <v-container class="py-8">
    <v-btn class="modern-run-btn w-100" size="large" @click="start">
      Start Connection
    </v-btn>
    <v-btn class="modern-run-btn w-100" size="large" @click="sendMsg">
      Send Message
    </v-btn>
    <v-btn class="modern-run-btn w-100" size="large" @click="stop">
      Stop Connection
    </v-btn>
  </v-container>
</template>

<script setup>

let pc = null
let dataChannel = null

async function stop() {
  await pc.close()
}
async function sendMsg() {
  dataChannel.send("ping - testing");
}


async function start() {
  console.log("Starting WebRTC connection...")

  const iceConfiguration = {
    iceServers: [
      {
        urls: ["stun:turn.codetam.com:3478"]
      },
      {
        urls: ["turn:turn.codetam.com:3478"],
        username: "user",
        credential: "my_static_secret"
      }]
  }

  pc = new RTCPeerConnection(iceConfiguration);

  pc.onconnectionstatechange = () => console.log("Pc connection state: " + pc.connectionState);

  dataChannel = pc.createDataChannel('chat', {
    ordered: true
  });

  dataChannel.onopen = () => {
    console.log('Data channel opened');

    setTimeout(() => {
      const testData = 'Handshake start';
      dataChannel.send(testData);
      console.log(`Sent: ${testData}`);
    }, 1000);
  };

  dataChannel.onmessage = (event) => {
    console.log(`Received: ${event.data}`);
  };

  dataChannel.onclose = () => {
    console.log('Data channel closed');
  };

  let offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  await new Promise((resolve) => {
    if (pc.iceGatheringState === 'complete') {
      resolve();
    } else {
      pc.addEventListener('icegatheringstatechange', () => {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        }
      });
    }
  });

  offer = pc.localDescription;
  const sessionId = Math.random().toString(36).slice(2); // random session id

  const resp = await fetch("http://localhost:8000/stream/webrtc/offer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sdp: offer.sdp,
      type: offer.type,
      session_id: sessionId
    })
  });
  console.log("Sent offer: " + JSON.stringify(offer))

  if (!resp.ok) {
    console.log("Failed to get answer: " + resp.status);
    return;
  }

  const answer = await resp.json();
  console.log("Got answer from server");
  console.log("Server responded: " + JSON.stringify(answer))

  pc.setRemoteDescription(answer);
}
</script>
