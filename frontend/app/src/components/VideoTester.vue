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
  dataChannel.send("Just sent a message!");
}


async function start() {
  const iceConfiguration = {
    iceServers = [
      { urls: "stun:stun.l.google.com:19302" },
      { urls: "stun:stun.l.google.com:5349" },
      { urls: "stun:stun1.l.google.com:3478" },
      { urls: "stun:stun1.l.google.com:5349" },
      { urls: "stun:stun2.l.google.com:19302" },
      { urls: "stun:stun2.l.google.com:5349" },
      { urls: "stun:stun3.l.google.com:3478" },
      { urls: "stun:stun3.l.google.com:5349" },
      { urls: "stun:stun4.l.google.com:19302" },
      { urls: "stun:stun4.l.google.com:5349" }
  ];

  pc = new RTCPeerConnection(iceConfiguration);

  pc.onconnectionstatechange = () => console.log("pc state: " + pc.connectionState);

  dataChannel = pc.createDataChannel('chat', {
    ordered: true
  });

  dataChannel.onopen = () => {
    console.log('Data channel opened');

    // Send test data after 1 second
    setTimeout(() => {
      const testData = 'Hello from JavaScript!';
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
  console.log(offer.sdp)

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
  console.log(offer.sdp)
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

  if (!resp.ok) {
    console.log("Failed to get answer: " + resp.status);
    return;
  }

  console.log(offer.sdp)
  const answer = await resp.json();
  console.log("Got answer from server");


  console.log(`OWN:`)
  console.log(JSON.stringify(offer))
  console.log(`SERVER:`)
  console.log(JSON.stringify(answer))
  
  pc.setRemoteDescription(answer);
}
</script>
