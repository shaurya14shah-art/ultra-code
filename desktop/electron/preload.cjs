const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  sendPrompt: (prompt) => ipcRenderer.send('send-prompt', prompt),
  onResponse: (callback) => ipcRenderer.on('ipc-response', (event, data) => callback(data)),
  onStreamChunk: (callback) => ipcRenderer.on('ipc-stream-chunk', (event, data) => callback(data)),
  onToolCall: (callback) => ipcRenderer.on('ipc-tool-call', (event, data) => callback(data)),
  
  // Clean up listeners
  removeAllListeners: () => {
    ipcRenderer.removeAllListeners('ipc-response');
    ipcRenderer.removeAllListeners('ipc-stream-chunk');
    ipcRenderer.removeAllListeners('ipc-tool-call');
  }
});
