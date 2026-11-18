/// <reference types="vite/client" />

interface Window {
  electron: {
    sendPrompt: (prompt: string) => void;
    onResponse: (callback: (data: string) => void) => void;
    onStreamChunk: (callback: (data: string) => void) => void;
    onToolCall: (callback: (data: any[]) => void) => void;
    removeAllListeners: () => void;
  };
}
