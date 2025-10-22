import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Sparkles, Send, ArrowLeft, Target, TrendingUp, FileText, Mail, Share2, Search, DollarSign, BarChart3, PieChart, Mic, MicOff, Volume2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AGENTS = [
  { id: "PlanningAgent", name: "Strategic Planning", icon: <Target />, color: "from-blue-500 to-blue-700", description: "Create marketing strategies and campaign plans" },
  { id: "MarketResearchAgent", name: "Market Research", icon: <TrendingUp />, color: "from-purple-500 to-purple-700", description: "Analyze markets, competitors, and trends" },
  { id: "ContentAgent", name: "Content Creation", icon: <FileText />, color: "from-pink-500 to-pink-700", description: "Generate trending content with viral potential" },
  { id: "EmailAgent", name: "Email Marketing", icon: <Mail />, color: "from-blue-600 to-indigo-700", description: "Design email campaigns and sequences" },
  { id: "SocialMediaAgent", name: "Social Media", icon: <Share2 />, color: "from-green-500 to-emerald-700", description: "Manage social media with auto-publishing" },
  { id: "SEOAgent", name: "SEO Optimization", icon: <Search />, color: "from-yellow-500 to-orange-600", description: "Optimize content for search engines" },
  { id: "PPCAgent", name: "PPC Advertising", icon: <DollarSign />, color: "from-red-500 to-red-700", description: "Create and optimize paid ad campaigns" },
  { id: "AnalyticsAgent", name: "Analytics", icon: <BarChart3 />, color: "from-indigo-500 to-indigo-700", description: "Analyze performance and provide insights" },
  { id: "ReportingAgent", name: "Reporting", icon: <PieChart />, color: "from-cyan-500 to-cyan-700", description: "Generate comprehensive reports" }
];

const AgentChatPage = () => {
  const navigate = useNavigate();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-select agent from URL parameter
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const agentId = params.get('agent');
    if (agentId) {
      const agent = AGENTS.find(a => a.id === agentId);
      if (agent) {
        setSelectedAgent(agent);
        toast.success(`Connected to ${agent.name}`);
      }
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize speech recognition and synthesis
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.lang = 'en-US';
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setMessage(transcript);
        setIsListening(false);
      };
      
      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
    
    synthRef.current = window.speechSynthesis;
    
    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
      if (synthRef.current) synthRef.current.cancel();
    };
  }, []);

  const startListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.start();
      setIsListening(true);
      toast.success('🎤 Listening...');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const speakText = (text) => {
    if (!synthRef.current) return;
    
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.05;
    
    const voices = synthRef.current.getVoices();
    const femaleVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Samantha'));
    if (femaleVoice) utterance.voice = femaleVoice;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    
    synthRef.current.speak(utterance);
  };

  const selectAgent = (agent) => {
    setSelectedAgent(agent);
    const welcomeMsg = `Hi! I'm your ${agent.name} specialist. How can I help you today?`;
    setMessages([{ role: "assistant", content: welcomeMsg }]);
    speakText(welcomeMsg);
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedAgent) return;

    const userMessage = message;
    setMessage("");
    setLoading(true);

    setMessages(prev => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await axios.post(`${API}/agent-chat`, {
        agent_id: selectedAgent.id,
        message: userMessage,
        messages: messages
      });

      const agentResponse = response.data.response;
      setMessages(prev => [...prev, {
        role: "assistant",
        content: agentResponse
      }]);
      
      speakText(agentResponse);

    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to get response from agent');
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pb-20">
      <nav className="glass fixed top-0 left-0 right-0 z-50 border-b border-white/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3" onClick={() => navigate('/')} style={{cursor: 'pointer'}}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              MarketAI
            </h1>
          </div>
          <Button 
            onClick={() => navigate('/')}
            variant="outline"
            className="border-cyan-200 hover:bg-cyan-50"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
        </div>
      </nav>

      <div className="pt-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold mb-3 text-slate-800">Talk to Our AI Agents</h1>
            <p className="text-lg text-slate-600">Select an agent for specialized voice/text assistance</p>
          </div>

          {!selectedAgent ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {AGENTS.map((agent) => (
                <Card
                  key={agent.id}
                  className="p-6 glass border-white/30 hover:shadow-2xl hover:-translate-y-1 transition-all cursor-pointer"
                  onClick={() => selectAgent(agent)}
                  data-testid={`agent-card-${agent.id}`}
                >
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center mb-4 text-white shadow-lg`}>
                    {agent.icon}
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-slate-800">{agent.name}</h3>
                  <p className="text-sm text-slate-600">{agent.description}</p>
                </Card>
              ))}
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              <Card className="glass border-white/30 shadow-xl">
                <div className="p-6 border-b border-white/20 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${selectedAgent.color} flex items-center justify-center text-white shadow-lg`}>
                      {selectedAgent.icon}
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-slate-800">{selectedAgent.name}</h2>
                      <p className="text-sm text-slate-600">{selectedAgent.description}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {isSpeaking && (
                      <Button variant="outline" size="sm" onClick={() => synthRef.current?.cancel()}>
                        <Volume2 className="w-4 h-4 mr-1" />
                        Stop
                      </Button>
                    )}
                    <Button variant="outline" size="sm" onClick={() => { setSelectedAgent(null); setMessages([]); }}>
                      Change Agent
                    </Button>
                  </div>
                </div>

                <div className="p-6 h-[500px] overflow-y-auto">
                  <div className="space-y-4">
                    {messages.map((msg, idx) => (
                      <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-4 rounded-2xl ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white'
                            : 'bg-white text-slate-800 shadow-md'
                        }`}>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    ))}
                    {loading && (
                      <div className="flex justify-start">
                        <div className="bg-white p-4 rounded-2xl shadow-md">
                          <div className="flex gap-2">
                            <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                </div>

                <div className="p-6 border-t border-white/20">
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={isListening ? stopListening : startListening}
                      disabled={loading}
                      className={isListening ? "bg-red-100 border-red-300" : ""}
                    >
                      {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </Button>
                    <Input
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                      placeholder="Type or speak your message..."
                      className="flex-1 bg-white"
                      disabled={loading}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={loading || !message.trim()}
                      className="bg-gradient-to-r from-cyan-500 to-blue-500"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500 mt-2 text-center">
                    {isListening ? '🎤 Listening...' : 'Click mic to speak or type your message'}
                  </p>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentChatPage;
