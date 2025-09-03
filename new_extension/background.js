let capturing = false;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "toggleCapture") {
    handleToggleCapture(sendResponse);
    return true; // Keep message channel open for async response
  } else if (message.action === "getStatus") {
    sendResponse({capturing: capturing});
  } else if (message.type === 'download-recording') {
    // Handle download from offscreen document
    chrome.downloads.download({
      url: message.url,
      filename: `recording_${Date.now()}.webm`,
      saveAs: true
    });
  }
});

async function handleToggleCapture(sendResponse) {
  try {
    if (capturing) {
      await stopCapture();
      sendResponse({capturing: false});
    } else {
      const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
      if (tab) {
        await startCapture(tab);
        sendResponse({capturing: true});
      } else {
        sendResponse({capturing: false, error: "No active tab found."});
      }
    }
  } catch (error) {
    console.error("Error toggling capture:", error);
    sendResponse({capturing: false, error: error.message});
  }
}

async function startCapture(tab) {
  console.log("Starting capture...");
  
  // Create offscreen document if it doesn't exist
  if (!(await chrome.offscreen.hasDocument())) {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA'],
      justification: 'Recording tab audio',
    });
  }

  // Get media stream ID
  const streamId = await chrome.tabCapture.getMediaStreamId({
    targetTabId: tab.id
  });

  // Send message to offscreen document to start recording
  chrome.runtime.sendMessage({
    type: 'start-recording',
    target: 'offscreen',
    data: streamId
  });

  capturing = true;
  console.log("Audio capture started.");
}

async function stopCapture() {
  console.log("Stopping capture...");
  
  try {
    if (await chrome.offscreen.hasDocument()) {
      // Send stop message before closing document
      chrome.runtime.sendMessage({
        type: 'stop-recording',
        target: 'offscreen'
      });
      
      // Wait a bit for the message to be processed
      setTimeout(async () => {
        try {
          await chrome.offscreen.closeDocument();
        } catch (e) {
          console.log("Document already closed or error closing:", e);
        }
      }, 100);
    }
  } catch (error) {
    console.error("Error in stopCapture:", error);
  }
  
  capturing = false;
  console.log("Audio capture stopped.");
}