import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sparkles, Mic, MicOff, ArrowLeft, Users, MessageSquare, Send, Target, TrendingUp, FileText, Mail, Share2, Search, DollarSign, BarChart3, PieChart, Video } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// All available agents with their configurations
const AGENTS = [
  {
    id: "PlanningAgent",
    name: "Strategic Planning",
    icon: Target,
    color: "from-blue-500 to-blue-700",
    description: "Create comprehensive marketing strategies and campaign plans",
    avatar: "🎯"
  },
  {
    id: "MarketResearchAgent",
    name: "Market Research",
    icon: TrendingUp,
    color: "from-purple-500 to-purple-700",
    description: "Analyze markets, competitors, and industry trends",
    avatar: "📊"
  },
  {
    id: "ContentAgent",
    name: "Content Creation",
    icon: FileText,
    color: "from-pink-500 to-pink-700",
    description: "Generate viral content and compelling copy",
    avatar: "✍️"
  },
  {
    id: "EmailAgent",
    name: "Email Marketing",
    icon: Mail,
    color: "from-blue-600 to-indigo-700",
    description: "Design high-converting email campaigns",
    avatar: "📧"
  },
  {
    id: "SocialMediaAgent",
    name: "Social Media",
    icon: Share2,
    color: "from-green-500 to-emerald-700",
    description: "Manage multi-platform social strategies",
    avatar: "📱"
  },
  {
    id: "SEOAgent",
    name: "SEO Optimization",
    icon: Search,
    color: "from-yellow-500 to-orange-600",
    description: "Drive organic traffic and rankings",
    avatar: "🔍"
  },
  {
    id: "PPCAgent",
    name: "PPC Advertising",
    icon: DollarSign,
    color: "from-red-500 to-red-700",
    description: "Optimize paid advertising campaigns",
    avatar: "💰"
  },
  {
    id: "AnalyticsAgent",
    name: "Analytics",
    icon: BarChart3,
    color: "from-indigo-500 to-indigo-700",
    description: "Analyze performance and provide insights",
    avatar: "📈"
  },
  {
    id: "ReportingAgent",
    name: "Reporting",
    icon: PieChart,
    color: "from-cyan-500 to-cyan-700",
    description: "Generate comprehensive reports",
    avatar: "📑"
  }
];

const UnifiedAgentChat = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Get agent from URL or default to first agent
  const agentIdFromUrl = searchParams.get('agent');
  const initialAgent = AGENTS.find(a => a.id === agentIdFromUrl) || AGENTS[0];

  const [currentAgent, setCurrentAgent] = useState(initialAgent);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [textMessage, setTextMessage] = useState("");
  const [isMinimized, setIsMinimized] = useState(false);

  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const messagesEndRef = useRef(null);
  const agentLogsEndRef = useRef(null);

  // Auto-scroll effects
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    agentLogsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentLogs]);

  // Update URL when agent changes
  useEffect(() => {
    if (currentAgent) {
      setSearchParams({ agent: currentAgent.id });
      // Clear messages when switching agents
      setMessages([]);
      setAgentLogs([]);
      addAgentLog('System', 'ACTIVATED', `Switched to ${currentAgent.name}`);
      toast.success(`Connected to ${currentAgent.name}`);
    }
  }, [currentAgent, setSearchParams]);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = selectedLanguage;

      recognitionRef.current.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        await processTranscript(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        setIsListening(false);
        if (event.error === 'no-speech') {
          toast.error('No speech detected. Please speak louder.');
        } else if (event.error === 'not-allowed') {
          toast.error('Microphone access denied.');
        }
      };

      recognitionRef.current.onend = () => setIsListening(false);
    }

    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
      if (synthRef.current) synthRef.current.cancel();
    };
  }, [selectedLanguage]);

  const startListening = () => {
    if (!recognitionRef.current) {
      toast.error('Speech recognition not supported. Use Chrome or Edge.');
      return;
    }

    try {
      recognitionRef.current.lang = selectedLanguage;
      recognitionRef.current.start();
      setIsListening(true);
      toast.success('🎤 Listening...');
    } catch (err) {
      toast.error('Failed to start listening.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setIsListening(false);
  };

  const addAgentLog = (agent, action, message) => {
    setAgentLogs(prev => [...prev, {
      agent,
      action,
      message,
      timestamp: new Date().toISOString()
    }]);
  };

  const processTranscript = async (transcript) => {
    if (!currentAgent) {
      toast.error('Please select an agent first');
      return;
    }

    try {
      setProcessing(true);

      // Add user message
      setMessages(prev => [...prev, { role: "user", content: transcript, timestamp: Date.now() }]);
      addAgentLog('User', 'MESSAGE', transcript.substring(0, 50) + '...');

      // Call agent-specific API
      const response = await axios.post(`${API}/agent-chat`, {
        agent_id: currentAgent.id,
        message: transcript,
        conversation_id: conversationId,
        user_id: "default_user"
      });

      if (!conversationId) {
        setConversationId(response.data.conversation_id || Date.now().toString());
      }

      const aiResponse = response.data.response || "I'm processing your request...";
      const imageData = response.data.image_base64;
      const videoConcept = response.data.video_concept;
      const promptUsed = response.data.prompt_used;

      // Add agent response
      setMessages(prev => [...prev, {
        role: "assistant",
        content: aiResponse,
        image: imageData,
        videoConcept: videoConcept,
        prompt: promptUsed,
        timestamp: Date.now()
      }]);

      addAgentLog(currentAgent.name, 'RESPONSE', 'Generated response');

      // Speak the response
      speakText(aiResponse);

    } catch (error) {
      console.error('Processing error:', error);
      toast.error('Failed to process your message.');
      addAgentLog('System', 'ERROR', `Failed: ${error.message}`);

      setMessages(prev => [...prev, {
        role: "assistant",
        content: `Sorry, I encountered an error. Please try again.`,
        timestamp: Date.now()
      }]);
    } finally {
      setProcessing(false);
    }
  };

  const speakText = (text) => {
    if (!synthRef.current) return;

    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = selectedLanguage;
    utterance.rate = 0.95;
    utterance.pitch = 1.05;

    const voices = synthRef.current.getVoices();
    const femaleVoice = voices.find(v =>
      v.lang.startsWith(selectedLanguage.split('-')[0]) &&
      (v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Victoria'))
    );

    if (femaleVoice) utterance.voice = femaleVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const handleSendTextMessage = async () => {
    if (!textMessage.trim() || processing) return;

    const messageToSend = textMessage;
    setTextMessage("");
    await processTranscript(messageToSend);
  };

  const IconComponent = currentAgent?.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg bg-black/30 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            {/* Agent Info */}
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${currentAgent?.color || 'from-cyan-500 to-blue-500'} flex items-center justify-center text-2xl animate-pulse`}>
                {currentAgent?.avatar || '🤖'}
              </div>
              <div className="text-left">
                <h2 className="text-white font-semibold">{currentAgent?.name || 'AI Agent'}</h2>
                <p className="text-xs text-slate-300">{currentAgent?.description || 'Specialized AI Assistant'}</p>
              </div>
            </div>

            {/* Agent Switcher */}
            <Select value={currentAgent?.id} onValueChange={(value) => {
              const agent = AGENTS.find(a => a.id === value);
              if (agent) setCurrentAgent(agent);
            }}>
              <SelectTrigger className="w-48 bg-white/10 text-white border-white/20">
                <SelectValue placeholder="Switch Agent" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-white/20">
                {AGENTS.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id} className="text-white hover:bg-white/10">
                    <div className="flex items-center gap-2">
                      <span>{agent.avatar}</span>
                      <span>{agent.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Language Selector */}
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-white/10 text-white border border-white/20 rounded-lg px-3 py-2 text-sm"
              style={{ colorScheme: 'dark' }}
            >
              <option value="en-US">🇺🇸 English</option>
              <option value="es-ES">🇪🇸 Spanish</option>
              <option value="fr-FR">🇫🇷 French</option>
              <option value="de-DE">🇩🇪 German</option>
              <option value="hi-IN">🇮🇳 Hindi</option>
            </select>
          </div>
        </div>
      </div>

      {/* Split Screen Layout */}
      <div className="pt-32 pb-24 px-6 h-screen">
        <div className="max-w-7xl mx-auto h-full grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* LEFT: User Conversation */}
          <Card className="backdrop-blur-lg bg-black/30 border-white/20 overflow-hidden flex flex-col">
            <div className="sticky top-0 z-10 backdrop-blur-lg bg-black/50 px-6 py-4 border-b border-white/20">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Your Conversation</h3>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${currentAgent?.color} flex items-center justify-center text-4xl mx-auto mb-4 animate-bounce`}>
                    {currentAgent?.avatar}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Welcome to {currentAgent?.name}!</h3>
                  <p className="text-slate-300">{currentAgent?.description}</p>
                  <p className="text-slate-400 text-sm mt-4">Start by typing or using voice input below</p>
                </div>
              )}

              {messages.map((msg, idx) => {
                const uniqueKey = `${msg.role}-${idx}-${msg.timestamp}`;

                return (
                  <div
                    key={uniqueKey}
                    className={`p-4 rounded-xl ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 ml-8'
                        : 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 mr-8'
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-300 mb-1">
                      {msg.role === 'user' ? 'You' : currentAgent?.name}
                    </p>
                    <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                    {/* Display image if available */}
                    {msg.image && (
                      <div className="mt-4">
                        <p className="text-xs text-green-400 mb-2">🎨 Generated Image:</p>
                        <img
                          src={`data:image/png;base64,${msg.image}`}
                          alt={msg.prompt || "Generated image"}
                          className="rounded-lg max-w-full h-auto border-2 border-white/20 shadow-lg"
                          onLoad={() => console.log('Image loaded successfully')}
                          onError={(e) => console.error('Image failed to load:', e)}
                        />
                        {msg.prompt && (
                          <p className="text-xs text-slate-400 mt-2 italic">
                            Prompt: {msg.prompt}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Display video concept if available */}
                    {msg.videoConcept && (
                      <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                        <p className="text-xs text-blue-400 mb-3 flex items-center gap-1 font-semibold">
                          <Video className="w-4 h-4" /> Video Concept Generated
                        </p>
                        <div className="space-y-2 text-xs text-slate-300">
                          {msg.videoConcept.video_concept && (
                            <p><span className="font-semibold text-blue-300">Concept:</span> {msg.videoConcept.video_concept}</p>
                          )}
                          {msg.videoConcept.duration_seconds && (
                            <p><span className="font-semibold text-blue-300">Duration:</span> {msg.videoConcept.duration_seconds}s</p>
                          )}
                          {msg.videoConcept.target_platform && (
                            <p><span className="font-semibold text-blue-300">Platform:</span> {msg.videoConcept.target_platform.join(', ')}</p>
                          )}
                          {msg.videoConcept.scenes && msg.videoConcept.scenes.length > 0 && (
                            <div className="mt-3">
                              <p className="font-semibold text-blue-300 mb-2">Scenes:</p>
                              {msg.videoConcept.scenes.slice(0, 3).map((scene, idx) => (
                                <div key={idx} className="ml-2 mb-2 p-2 bg-black/20 rounded">
                                  <p className="text-blue-200">Scene {scene.scene_number}: {scene.description?.substring(0, 100)}...</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          </Card>

          {/* RIGHT: Agent Communication */}
          <Card className="backdrop-blur-lg bg-black/30 border-white/20 overflow-hidden flex flex-col">
            <div className="sticky top-0 z-10 backdrop-blur-lg bg-black/50 px-6 py-4 border-b border-white/20">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">Agent Activity</h3>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {agentLogs.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">Agent activity will appear here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {agentLogs.map((log, idx) => (
                    <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10 animate-fade-in">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-purple-400">{log.agent}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          log.action === 'RESPONSE' ? 'bg-green-500/20 text-green-400' :
                          log.action === 'ERROR' ? 'bg-red-500/20 text-red-400' :
                          log.action === 'ACTIVATED' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {log.action}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300">{log.message}</p>
                    </div>
                  ))}
                  <div ref={agentLogsEndRef} />
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Compact Voice Control & Text Input */}
      <div className="fixed bottom-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-6 pb-4">
          <Card className={`backdrop-blur-2xl bg-black/40 border-white/20 shadow-2xl transition-all duration-300 ${
            isMinimized ? 'p-2' : 'p-4'
          }`}>
            {!isMinimized ? (
              /* Expanded Mode */
              <div className="flex gap-3 items-center">
                {/* Text Input */}
                <Input
                  value={textMessage}
                  onChange={(e) => setTextMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendTextMessage()}
                  placeholder={`Ask ${currentAgent?.name || 'agent'} anything...`}
                  className="flex-1 bg-white/10 text-white border-white/20 placeholder:text-slate-400 h-12"
                  disabled={processing}
                />

                {/* Send Button */}
                <Button
                  onClick={handleSendTextMessage}
                  disabled={processing || !textMessage.trim()}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 h-12 px-4"
                >
                  <Send className="w-5 h-5" />
                </Button>

                {/* Mic Button */}
                <Button
                  size="lg"
                  disabled={processing || isSpeaking}
                  onClick={isListening ? stopListening : startListening}
                  className={`h-12 w-12 rounded-full ${
                    isListening
                      ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse'
                      : 'bg-gradient-to-br from-cyan-500 to-blue-500'
                  } shadow-lg`}
                  title={isListening ? 'Stop listening' : 'Start voice input'}
                >
                  {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </Button>

                {/* Stop Speaking Button */}
                {isSpeaking && (
                  <Button
                    onClick={stopSpeaking}
                    className="h-12 w-12 rounded-full bg-gradient-to-br from-orange-500 to-red-500 shadow-lg"
                    title="Stop speaking"
                  >
                    <span className="text-lg">⏸️</span>
                  </Button>
                )}

                {/* Minimize Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMinimized(true)}
                  className="text-white hover:bg-white/10 h-12 px-3"
                  title="Minimize"
                >
                  <span className="text-xs">▼</span>
                </Button>

                {/* Status Indicator */}
                <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-white/20">
                  <div className={`w-2 h-2 rounded-full ${
                    isListening ? 'bg-red-500 animate-pulse' :
                    isSpeaking ? 'bg-orange-500 animate-pulse' :
                    processing ? 'bg-yellow-500 animate-pulse' :
                    'bg-green-500'
                  }`} />
                  <span className="text-xs text-slate-300">
                    {isListening ? 'Listening' : isSpeaking ? 'Speaking' : processing ? 'Processing' : 'Ready'}
                  </span>
                </div>
              </div>
            ) : (
              /* Minimized Mode */
              <div className="flex items-center justify-end gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMinimized(false)}
                  className="text-white hover:bg-white/10 text-xs"
                >
                  Expand ▲
                </Button>

                <Button
                  size="sm"
                  disabled={processing || isSpeaking}
                  onClick={isListening ? stopListening : startListening}
                  className={`h-10 w-10 rounded-full ${
                    isListening
                      ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse'
                      : 'bg-gradient-to-br from-cyan-500 to-blue-500'
                  } shadow-lg`}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default UnifiedAgentChat;
