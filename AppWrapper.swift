import Cocoa
import WebKit
import Foundation

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKScriptMessageHandler {
    var window: NSWindow!
    var webView: WKWebView!
    var timer: Timer?
    var lastTranscriptLineCount = 0
    
    let workspaceDir = "/Users/shauryashah/AG/ultra-code"
    
    var ipcRequestPath: String { return workspaceDir + "/.ipc_request.txt" }
    var ipcResponsePath: String { return workspaceDir + "/.ipc_response.txt" }
    var ipcStreamPath: String { return workspaceDir + "/.ipc_stream.txt" }
    var transcriptPath: String { 
        return FileManager.default.homeDirectoryForCurrentUser.path + "/.gemini/antigravity-ide/brain/40298de1-2b41-4efb-b0a0-16c392e01494/.system_generated/logs/transcript.jsonl"
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        let rect = NSRect(x: 0, y: 0, width: 1200, height: 800)
        
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "UltraCode Native"
        window.titlebarAppearsTransparent = true
        window.backgroundColor = NSColor(calibratedRed: 0.04, green: 0.04, blue: 0.04, alpha: 1.0)
        window.delegate = self
        
        let webConfiguration = WKWebViewConfiguration()
        let contentController = WKUserContentController()
        contentController.add(self, name: "swiftHandler")
        webConfiguration.userContentController = contentController
        
        // Expose a global dispatchEvent helper early
        let scriptSource = """
            window.dispatchSwiftEvent = function(eventName, data) {
                const event = new CustomEvent(eventName, { detail: data });
                window.dispatchEvent(event);
            };
        """
        let userScript = WKUserScript(source: scriptSource, injectionTime: .atDocumentStart, forMainFrameOnly: true)
        webConfiguration.userContentController.addUserScript(userScript)
        
        webView = WKWebView(frame: rect, configuration: webConfiguration)
        webView.setValue(false, forKey: "drawsBackground") // Transparent background
        
        window.contentView = webView
        window.makeKeyAndOrderFront(nil)
        
        // Load Vite Server
        if let url = URL(string: "http://127.0.0.1:5173") {
            let request = URLRequest(url: url)
            webView.load(request)
        }
        
        NSApp.activate(ignoringOtherApps: true)
        
        // Start IPC Polling
        timer = Timer.scheduledTimer(timeInterval: 0.3, target: self, selector: #selector(pollIPC), userInfo: nil, repeats: true)
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "swiftHandler", let dict = message.body as? [String: Any], let type = dict["type"] as? String {
            if type == "send-prompt", let prompt = dict["payload"] as? String {
                do {
                    try prompt.write(toFile: ipcRequestPath, atomically: true, encoding: .utf8)
                } catch {
                    print("Error writing prompt: \(error)")
                }
            }
        }
    }
    
    @objc func pollIPC() {
        // 1. Check for complete response
        if FileManager.default.fileExists(atPath: ipcResponsePath) {
            do {
                let data = try String(contentsOfFile: ipcResponsePath, encoding: .utf8)
                try FileManager.default.removeItem(atPath: ipcResponsePath)
                sendToWebView(event: "ipc-response", data: data)
            } catch {}
        }
        
        // 2. Check for stream chunks
        if FileManager.default.fileExists(atPath: ipcStreamPath) {
            do {
                let data = try String(contentsOfFile: ipcStreamPath, encoding: .utf8)
                if !data.isEmpty {
                    try "".write(toFile: ipcStreamPath, atomically: true, encoding: .utf8)
                    sendToWebView(event: "ipc-stream-chunk", data: data)
                }
            } catch {}
        }
        
        // 3. Tail transcript for tools
        if FileManager.default.fileExists(atPath: transcriptPath) {
            do {
                let content = try String(contentsOfFile: transcriptPath, encoding: .utf8)
                let lines = content.components(separatedBy: .newlines).filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
                
                if lines.count > lastTranscriptLineCount {
                    for i in lastTranscriptLineCount..<lines.count {
                        let line = lines[i]
                        // Just pass the JSON string directly to the JS parser
                        if line.contains("PLANNER_RESPONSE") && line.contains("tool_calls") {
                            sendJSONToWebView(event: "ipc-tool-call", jsonString: line)
                        }
                    }
                    lastTranscriptLineCount = lines.count
                }
            } catch {}
        }
    }
    
    func sendToWebView(event: String, data: String) {
        // Escape special chars for evaluateJavaScript
        let escapedData = data.replacingOccurrences(of: "\\", with: "\\\\")
                              .replacingOccurrences(of: "\"", with: "\\\"")
                              .replacingOccurrences(of: "\n", with: "\\n")
                              .replacingOccurrences(of: "\r", with: "\\r")
        let js = "window.dispatchSwiftEvent('\(event)', \"\(escapedData)\");"
        DispatchQueue.main.async {
            self.webView.evaluateJavaScript(js, completionHandler: nil)
        }
    }
    
    func sendJSONToWebView(event: String, jsonString: String) {
        // Here we just pass the raw JSON string as an object if we parse it, but it's safer to pass as string and JSON.parse in JS
        let escapedData = jsonString.replacingOccurrences(of: "\\", with: "\\\\")
                              .replacingOccurrences(of: "\"", with: "\\\"")
                              .replacingOccurrences(of: "\n", with: "\\n")
        let js = "try { const obj = JSON.parse(\"\(escapedData)\"); if(obj.tool_calls) window.dispatchSwiftEvent('\(event)', obj.tool_calls); } catch(e) {}"
        DispatchQueue.main.async {
            self.webView.evaluateJavaScript(js, completionHandler: nil)
        }
    }

    func windowWillClose(_ notification: Notification) {
        NSApplication.shared.terminate(self)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
