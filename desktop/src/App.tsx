import { useState, useEffect, useRef } from 'react';
import { Send, Settings, Zap, Compass, Cog, Palette, Shield, Search, BookOpen, Layers } from 'lucide-react';
import './index.css';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

const ULTRCODE_AGENTS = [
  { id: 'architect', avatar: './agents/architect.png', icon: <Compass size={16} />, name: 'Architect', role: 'Planner', color: 'text-purple-400', dot: 'bg-purple-500', activeBg: 'rgba(168, 85, 247, 0.15)', activeBorder: 'rgba(168, 85, 247, 0.4)' },
  { id: 'builder-a', avatar: './agents/builder-a.png', icon: <Cog size={16} />, name: 'Builder-α', role: 'Backend', color: 'text-blue-400', dot: 'bg-blue-500', activeBg: 'rgba(59, 130, 246, 0.15)', activeBorder: 'rgba(59, 130, 246, 0.4)' },
  { id: 'builder-b', avatar: './agents/builder-b.png', icon: <Palette size={16} />, name: 'Builder-β', role: 'Frontend', color: 'text-pink-400', dot: 'bg-pink-500', activeBg: 'rgba(236, 72, 153, 0.15)', activeBorder: 'rgba(236, 72, 153, 0.4)' },
  { id: 'sentinel', avatar: './agents/sentinel.png', icon: <Shield size={16} />, name: 'Sentinel', role: 'Testing QA', color: 'text-emerald-400', dot: 'bg-emerald-500', activeBg: 'rgba(16, 185, 129, 0.15)', activeBorder: 'rgba(16, 185, 129, 0.4)' },
  { id: 'auditor', avatar: './agents/auditor.png', icon: <Search size={16} />, name: 'Auditor', role: 'Reviewer', color: 'text-amber-400', dot: 'bg-amber-500', activeBg: 'rgba(245, 158, 11, 0.15)', activeBorder: 'rgba(245, 158, 11, 0.4)' },
  { id: 'scribe', avatar: './agents/scribe.png', icon: <BookOpen size={16} />, name: 'Scribe', role: 'Integrator', color: 'text-cyan-400', dot: 'bg-cyan-500', activeBg: 'rgba(6, 182, 212, 0.15)', activeBorder: 'rgba(6, 182, 212, 0.4)' },
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [swarmMode, setSwarmMode] = useState(true);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());
  const [deployedAgents, setDeployedAgents] = useState<Set<string>>(new Set());
  const [taskProgress, setTaskProgress] = useState(0);
  const [subAgentsCount, setSubAgentsCount] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentAgentMessageRef = useRef<string>('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isProcessing && swarmMode) {
      setTaskProgress(0);
      setSubAgentsCount(0);
      interval = setInterval(() => {
        setTaskProgress(prev => Math.min(prev + (Math.random() * 3), 98));
        setSubAgentsCount(prev => Math.min(prev + Math.floor(Math.random() * 5), 100));
      }, 400);
    } else if (!isProcessing && swarmMode && taskProgress > 0) {
      setTaskProgress(100);
      setSubAgentsCount(100);
    }
    return () => clearInterval(interval);
  }, [isProcessing, swarmMode]);

  useEffect(() => {
    // Setup Electron IPC listeners if running in Electron
    if (window.electron) {
      window.electron.onResponse((data: string) => {
        setMessages(prev => {
          const newMessages = [...prev];
          if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'agent') {
            newMessages[newMessages.length - 1].content = data;
          } else {
            newMessages.push({ role: 'agent', content: data });
          }
          return newMessages;
        });
        setIsProcessing(false);
        setStatus('Ready');
        setActiveAgents(new Set());
        setDeployedAgents(new Set());
        currentAgentMessageRef.current = '';
      });

      window.electron.onStreamChunk((data: string) => {
        currentAgentMessageRef.current += data;
        setMessages(prev => {
          const newMessages = [...prev];
          if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'agent') {
            newMessages[newMessages.length - 1].content = currentAgentMessageRef.current;
          } else {
            newMessages.push({ role: 'agent', content: currentAgentMessageRef.current });
          }
          return newMessages;
        });
      });

      window.electron.onToolCall((tools: any[]) => {
        const newActive = new Set<string>();
        tools.forEach(tool => {
          const toolName = tool.name;
          const args = tool.arguments || {};
          let target = args.TargetFile || args.AbsolutePath || args.CommandLine || args.DirectoryPath || args.Query || '';
          
          let agentId = 'architect'; // default
          if (toolName.includes('replace') || toolName.includes('write')) {
            if (target.endsWith('.tsx') || target.endsWith('.css') || target.endsWith('.html') || target.endsWith('.ts')) {
              agentId = 'builder-b';
            } else {
              agentId = 'builder-a';
            }
          } else if (toolName === 'run_command') {
            if (target.includes('test') || target.includes('lint')) {
              agentId = 'sentinel';
            } else {
              agentId = 'builder-a';
            }
          } else if (toolName.includes('grep') || toolName.includes('view') || toolName.includes('list')) {
            agentId = 'auditor';
          }
          
          newActive.add(agentId);

          let displayTarget = '...';
          let formatted = `\n> 🛠️ **${toolName}**`;
          
          if (toolName === 'multi_replace_file_content' || toolName === 'replace_file_content') {
            displayTarget = args.TargetFile ? args.TargetFile.split('/').pop() : '...';
            formatted += `: \`${displayTarget}\`\n`;
          } else if (toolName === 'run_command') {
            displayTarget = args.CommandLine || '...';
            formatted += `: \`${displayTarget}\`\n`;
          } else if (toolName === 'view_file' || toolName === 'write_to_file') {
            displayTarget = (args.AbsolutePath || args.TargetFile || '...').split('/').pop() || '...';
            formatted += `: \`${displayTarget}\`\n`;
          } else {
            displayTarget = target;
            formatted += `: \`${displayTarget}\`\n`;
          }

          currentAgentMessageRef.current += formatted;
        });

        if (newActive.size > 0) {
          setActiveAgents(newActive);
          setDeployedAgents(prev => {
            const next = new Set(prev);
            newActive.forEach(id => next.add(id));
            return next;
          });
        }
          
          setMessages(prev => {
            const newMessages = [...prev];
            if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'agent') {
              newMessages[newMessages.length - 1].content = currentAgentMessageRef.current;
            } else {
              newMessages.push({ role: 'agent', content: currentAgentMessageRef.current });
            }
            return newMessages;
          });
      });
    }

    return () => {
      if (window.electron) window.electron.removeAllListeners();
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const command = input.trim().toLowerCase();

    // Save exactly what the user typed for UI
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setIsProcessing(true);
    setStatus(swarmMode ? 'Swarm Initiated...' : 'Working...');
    
    if (command === 's1') {
      if (window.electron) {
        window.electron.sendPrompt('s1');
      } else {
        window.location.reload();
      }
      setTimeout(() => {
        setIsProcessing(false);
        setStatus('Ready');
      }, 1000);
      setInput('');
      currentAgentMessageRef.current = '';
      return;
    }

    // Prefix with /ultracode if swarm mode is active
    const finalPrompt = swarmMode ? `/ultracode ${input}` : input;

    if (window.electron) {
      window.electron.sendPrompt(finalPrompt);
    } else {
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'agent', content: `Mock response for: ${finalPrompt}` }]);
        setIsProcessing(false);
        setStatus('Ready');
      }, 1500);
    }
    
    setInput('');
    currentAgentMessageRef.current = '';
  };

  return (
    <div className="flex h-screen bg-[#050505] text-[#f3f4f6]">
      {/* Sidebar */}
      <div className="w-72 glass-panel border-r border-white/10 flex flex-col draggable-header z-10">
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="text-blue-500 animate-pulse-glow rounded-full" size={22} />
            <h1 className="font-bold tracking-widest text-lg bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300">ULTRACODE</h1>
          </div>
        </div>
        
        <div className="flex-1 p-4 overflow-y-auto non-draggable space-y-6">
          
          {/* Swarm Mode Toggle */}
          <div className="bg-white/5 rounded-xl p-4 border border-white/10 flex items-center justify-between hover:bg-white/10 transition-colors">
            <div className="flex items-center gap-3">
              <Layers className={swarmMode ? "text-emerald-400" : "text-white/40"} size={18} />
              <div>
                <div className="text-sm font-semibold text-white/90">Swarm Mode</div>
                <div className="text-xs text-white/50">Multi-agent delegation</div>
              </div>
            </div>
            <button 
              onClick={() => setSwarmMode(!swarmMode)}
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center ${swarmMode ? 'bg-emerald-500' : 'bg-white/20'}`}
            >
              <div className={`w-4 h-4 bg-white rounded-full absolute shadow-sm transition-transform ${swarmMode ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>

          <div>
            <div className="mb-4">
              <div className="flex justify-between items-center text-xs font-semibold text-white/50 mb-1.5 px-2 uppercase tracking-wider">
                <span>Deployed Agents</span>
                <span>{isProcessing && swarmMode ? `${Math.max(1, deployedAgents.size)}/6` : '0/6'}</span>
              </div>
              <div className="px-2">
                <div className="deployment-bar-container">
                  <div className="deployment-bar-fill" style={{ width: (isProcessing && swarmMode) ? `${(Math.max(1, deployedAgents.size) / 6) * 100}%` : '0%' }}></div>
                </div>
              </div>
            </div>

            <div className="text-xs font-semibold text-white/40 mb-3 uppercase tracking-wider pl-2 flex items-center gap-2">
              Agent Constellation
              {isProcessing && swarmMode && <span className="flex h-2 w-2 relative"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span></span>}
            </div>
            <div className="space-y-2">
              {ULTRCODE_AGENTS.map((agent, i) => {
                const isActive = isProcessing && swarmMode && (activeAgents.has(agent.id) || (activeAgents.size === 0 && agent.id === 'architect'));
                return (
                  <div 
                    key={agent.id}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-500 ease-in-out ${isActive ? 'agent-active' : 'hover:bg-white/5 bg-transparent'}`}
                    style={isActive ? { 
                      backgroundColor: agent.activeBg,
                      borderColor: agent.activeBorder,
                      animationDelay: `${i * 0.1}s`
                    } : {}}
                  >
                    <div className={`p-1.5 rounded-lg bg-white/5 relative flex items-center justify-center`}>
                      <img src={agent.avatar} alt={agent.name} className={`chibi-avatar ${isActive ? 'active' : ''}`} style={{ color: isActive ? agent.activeBorder : 'transparent' }} />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white/90">{agent.name}</span>
                      <span className="text-[10px] text-white/40 uppercase tracking-widest">{agent.role}</span>
                    </div>
                    {isActive ? (
                      <div className="ml-auto flex gap-1">
                        <div className={`w-1 h-3 ${agent.dot} animate-pulse rounded-full`} style={{animationDelay: '0s'}}></div>
                        <div className={`w-1 h-3 ${agent.dot} animate-pulse rounded-full`} style={{animationDelay: '0.2s'}}></div>
                        <div className={`w-1 h-3 ${agent.dot} animate-pulse rounded-full`} style={{animationDelay: '0.4s'}}></div>
                      </div>
                    ) : (
                      <div className={`w-1.5 h-1.5 rounded-full ml-auto ${agent.dot} opacity-30`}></div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-white/10 text-xs text-white/40 flex items-center gap-2 non-draggable cursor-pointer hover:text-white/80 transition-colors bg-white/5">
          <Settings size={14} />
          <span>System Preferences</span>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] bg-opacity-20">
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 non-draggable pb-32">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-white/30 animate-float">
              <Zap size={64} className="mb-6 opacity-20 text-blue-500" />
              <h2 className="text-xl font-semibold text-white/50 mb-2">UltraCode Orchestrator</h2>
              <p className="text-sm text-center max-w-md">
                Enable Swarm Mode to deploy the 6-agent constellation for massive parallel engineering tasks.
              </p>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
              <div className={`max-w-[85%] p-5 rounded-2xl shadow-xl ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-blue-600 to-blue-800 text-white ml-12 rounded-tr-sm border border-blue-500/30' 
                  : 'agent-card text-white/90 mr-12 rounded-tl-sm font-mono text-sm leading-relaxed whitespace-pre-wrap'
              }`}>
                {msg.role === 'agent' && (
                  <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/10 text-xs uppercase tracking-widest text-blue-400 font-sans font-semibold">
                    <Zap size={14} />
                    Agent Response
                  </div>
                )}
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 p-6 pt-12 non-draggable bg-gradient-to-t from-[#050505] via-[#050505] to-transparent">
          <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
            
            {/* Hovering Ghibli Characters & Progress Bars */}
            <div className={`transition-all duration-700 overflow-hidden ${isProcessing && swarmMode ? 'opacity-100 translate-y-0 h-28 mb-4' : 'opacity-0 translate-y-4 h-0 mb-0'}`}>
              <div className="flex flex-col gap-2 px-4">
                {/* Ghibli Characters */}
                <div className="flex items-center gap-1.5 mb-1">
                  {ULTRCODE_AGENTS.map((agent, idx) => (
                    <img 
                      key={agent.id} 
                      src={agent.avatar} 
                      alt={agent.name} 
                      className="w-7 h-7 rounded-full border border-white/20 object-cover shadow-lg animate-bounce"
                      style={{ animationDelay: `${idx * 0.15}s`, animationDuration: '1s' }} 
                    />
                  ))}
                  <div className="text-[10px] font-mono text-white/50 ml-3 animate-pulse">Spawning multi-agent hive...</div>
                </div>
                
                {/* Progress Bars */}
                <div className="flex flex-col gap-2 bg-white/5 p-3 rounded-xl border border-white/10 backdrop-blur-md">
                  <div>
                    <div className="flex items-center justify-between text-[9px] uppercase font-bold tracking-widest text-white/50 mb-1.5">
                      <span className="flex items-center gap-1.5"><Cog size={10} className="animate-spin" /> Task Progress</span>
                      <span>{Math.floor(taskProgress)}%</span>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden shadow-inner">
                      <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-300" style={{ width: `${taskProgress}%` }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between text-[9px] uppercase font-bold tracking-widest text-white/50 mb-1.5">
                      <span className="flex items-center gap-1.5"><Layers size={10} /> Sub-Agents Deployed</span>
                      <span>{Math.floor(subAgentsCount)} / 100</span>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden shadow-inner">
                      <div className="h-full bg-gradient-to-r from-emerald-500 to-green-400 rounded-full transition-all duration-300" style={{ width: `${subAgentsCount}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className={`absolute -inset-1 rounded-2xl blur opacity-20 transition duration-1000 ${isProcessing ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 animate-pulse-glow' : ''}`}></div>
            <div className="relative flex items-center bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl focus-within:border-blue-500/50 focus-within:bg-[#0f0f0f] transition-all">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder={swarmMode ? "Deploy the swarm... (s1=reload, s2=memory)" : "Message UltraCode directly..."}
                disabled={isProcessing}
                className="w-full bg-transparent py-4 pl-5 pr-14 outline-none text-white placeholder:text-white/30 disabled:opacity-50"
              />
              <button 
                type="submit" 
                disabled={!input.trim() || isProcessing}
                className="absolute right-3 p-2.5 bg-blue-600 rounded-xl text-white disabled:opacity-40 disabled:bg-white/10 hover:bg-blue-500 transition-all hover:scale-105 active:scale-95"
              >
                <Send size={18} />
              </button>
            </div>
          </form>
          <div className="text-center mt-3 text-[10px] text-white/30 uppercase tracking-widest font-semibold">
            {status}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
