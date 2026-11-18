// Native Swift WKWebView IPC Polyfill
// This replaces the Electron preload script and routes messages to AppWrapper.swift

window.electron = {
  sendPrompt: (prompt) => {
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.swiftHandler) {
      window.webkit.messageHandlers.swiftHandler.postMessage({ type: 'send-prompt', payload: prompt });
    } else {
      console.warn("Swift handler not found. Are you running inside the Native AppWrapper?");
    }
  },
  
  onResponse: (callback) => {
    window.addEventListener('ipc-response', (e) => {
      callback(e.detail);
    });
  },
  
  onStreamChunk: (callback) => {
    window.addEventListener('ipc-stream-chunk', (e) => {
      callback(e.detail);
    });
  },
  
  onToolCall: (callback) => {
    window.addEventListener('ipc-tool-call', (e) => {
      callback(e.detail);
    });
  },
  
  removeAllListeners: () => {
    // We don't easily remove anonymous listeners with addEventListener unless we keep a reference.
    // For this prototype, we'll just let React clean up components, or we could implement a listener registry.
  }
};
