document.addEventListener('DOMContentLoaded', function() {
  const captureButton = document.getElementById('captureButton');
  const statusDiv = document.getElementById('status');

  captureButton.addEventListener('click', function() {
    statusDiv.textContent = 'Processing...';
    captureButton.disabled = true;
    
    chrome.runtime.sendMessage({action: "toggleCapture"}, function(response) {
      captureButton.disabled = false;
      
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError.message);
        statusDiv.textContent = 'Error: ' + chrome.runtime.lastError.message;
        return;
      }
      
      if (response.error) {
        statusDiv.textContent = 'Error: ' + response.error;
        return;
      }
      
      if (response.capturing) {
        captureButton.textContent = 'Stop Capture';
        captureButton.className = 'stop';
        statusDiv.textContent = 'Recording...';
      } else {
        captureButton.textContent = 'Start Capture';
        captureButton.className = 'start';
        statusDiv.textContent = 'Recording saved!';
      }
    });
  });

  // Set initial button state
  chrome.runtime.sendMessage({action: "getStatus"}, function(response) {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError.message);
      statusDiv.textContent = 'Error getting status';
      return;
    }
    
    if (response.capturing) {
      captureButton.textContent = 'Stop Capture';
      captureButton.className = 'stop';
      statusDiv.textContent = 'Recording...';
    } else {
      captureButton.textContent = 'Start Capture';
      captureButton.className = 'start';
      statusDiv.textContent = 'Ready';
    }
  });
});