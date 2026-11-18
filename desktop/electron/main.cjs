const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

const IS_DEV = process.env.NODE_ENV === 'development';
const WORKSPACE_DIR = '/Users/USER/AG/ultra-code';
const IPC_REQUEST_PATH = path.join(WORKSPACE_DIR, '.ipc_request.txt');
const IPC_RESPONSE_PATH = path.join(WORKSPACE_DIR, '.ipc_response.txt');
const IPC_STREAM_PATH = path.join(WORKSPACE_DIR, '.ipc_stream.txt');
const TRANSCRIPT_PATH = path.join(
  require('os').homedir(), 
  '.gemini', 'antigravity-ide', 'brain', 
  '40298de1-2b41-4efb-b0a0-16c392e01494', 
  '.system_generated', 'logs', 'transcript.jsonl'
);

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0a0a0a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (IS_DEV) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Watch for IPC Responses and Stream Updates
let lastLineCount = 0;

setInterval(() => {
  if (!mainWindow) return;

  // 1. Check for complete response
  if (fs.existsSync(IPC_RESPONSE_PATH)) {
    try {
      const data = fs.readFileSync(IPC_RESPONSE_PATH, 'utf8');
      fs.unlinkSync(IPC_RESPONSE_PATH);
      mainWindow.webContents.send('ipc-response', data);
    } catch (e) {}
  }

  // 2. Check for stream chunks
  if (fs.existsSync(IPC_STREAM_PATH)) {
    try {
      const data = fs.readFileSync(IPC_STREAM_PATH, 'utf8');
      if (data) {
        fs.writeFileSync(IPC_STREAM_PATH, ''); // Clear it
        mainWindow.webContents.send('ipc-stream-chunk', data);
      }
    } catch (e) {}
  }

  // 3. Tail transcript for tools
  if (fs.existsSync(TRANSCRIPT_PATH)) {
    try {
      const lines = fs.readFileSync(TRANSCRIPT_PATH, 'utf8').split('\n').filter(l => l.trim());
      if (lines.length > lastLineCount) {
        for (let i = lastLineCount; i < lines.length; i++) {
          try {
            const data = JSON.parse(lines[i]);
            if (data.type === 'PLANNER_RESPONSE' && data.tool_calls) {
              mainWindow.webContents.send('ipc-tool-call', data.tool_calls);
            }
          } catch(e) {}
        }
        lastLineCount = lines.length;
      }
    } catch (e) {}
  }

}, 300);

const { exec } = require('child_process');

ipcMain.on('send-prompt', (event, prompt) => {
  const p = prompt.trim().toLowerCase();
  
  if (p === 's1' || p === '/ultracode s1') {
    if (mainWindow) mainWindow.reload();
    return;
  }
  
  if (p === 's2' || p === '/ultracode s2') {
    const scriptPath = path.join(require('os').homedir(), '.gemini/config/skills/obsidian-terminal-memory/scripts/visualize_graph.py');
    exec(`python3 "${scriptPath}"`, (error, stdout, stderr) => {
      const output = error ? (stderr || error.message) : stdout;
      if (mainWindow) mainWindow.webContents.send('ipc-response', output);
    });
    return;
  }

  fs.writeFileSync(IPC_REQUEST_PATH, prompt);
});
