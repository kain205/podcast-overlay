let recorder;
let data = [];
let mediaStream;
let socket;

function connectWebSocket() {
  socket = new WebSocket("ws://localhost:8765"); // Python WebSocket server

  socket.onopen = () => {
    console.log("WebSocket connected");
  };

  socket.onclose = () => {
    console.log("WebSocket closed, reconnecting...");
    setTimeout(connectWebSocket, 2000); // reconnect nếu mất
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
  };
}
connectWebSocket();

chrome.runtime.onMessage.addListener((message) => {
  if (message.target === 'offscreen') {
    if (message.type === 'start-recording') {
      startRecording(message.data);
    } else if (message.type === 'stop-recording') {
      stopRecording();
    }
  }
});

async function startRecording(streamId) {
  console.log("Offscreen: Starting recording with streamId:", streamId);
  
  try {
    // Clear any previous data
    data = [];
    
    // Get media stream
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId
        }
      },
      video: false
    });

    console.log("Offscreen: Media stream obtained");

    // Create recorder
    recorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
    
    recorder.ondataavailable = async (event) => {
      if (event.data.size > 0 && socket && socket.readyState == WebSocket.OPEN) {
        const arrayBuffer = await event.data.arrayBuffer();
        socket.send(arrayBuffer);
        console.log("Chunk sent, size:", arrayBuffer.byteLength);
      }
    };
    
    recorder.onstop = () => {
      console.log("Offscreen: Recorder stopped, creating blob...");
      
      if (data.length > 0) {
        const blob = new Blob(data, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        
        console.log("Offscreen: Blob created, size:", blob.size);
        
        // Send download message to background script
        chrome.runtime.sendMessage({ 
          type: 'download-recording', 
          url: url 
        });
        
        // Clean up
        setTimeout(() => {
          URL.revokeObjectURL(url);
        }, 1000);
      } else {
        console.log("Offscreen: No data recorded");
      }
      
      // Clean up
      data = [];
      recorder = null;
      
      // Stop media stream tracks
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => {
          track.stop();
          console.log("Offscreen: Track stopped:", track.kind);
        });
        mediaStream = null;
      }
    };

    recorder.onerror = (event) => {
      console.error("Offscreen: Recorder error:", event.error);
    };

    // Start recording
    recorder.start(1000); // Collect data every second
    console.log("Offscreen: Recording started");

  } catch (error) {
    console.error("Offscreen: Error starting recording:", error);
  }
}

function stopRecording() {
  console.log("Offscreen: Stop recording requested");
  
  try {
    if (recorder && recorder.state === 'recording') {
      recorder.stop();
      console.log("Offscreen: Recorder stopped");
    } else {
      console.log("Offscreen: No active recorder to stop");
      
      // Clean up anyway
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
      }
    }
  } catch (error) {
    console.error("Offscreen: Error stopping recorder:", error);
  }
}