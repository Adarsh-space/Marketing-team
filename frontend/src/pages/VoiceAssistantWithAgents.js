import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Sparkles, Mic, MicOff, ArrowLeft, Users, MessageSquare, Send } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VoiceAssistantWithAgents = () => {
  const navigate = useNavigate();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [currentAgent, setCurrentAgent] = useState(null);
  const [textMessage, setTextMessage] = useState("");
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const messagesEndRef = useRef(null);
  const agentLogsEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    agentLogsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentLogs]);

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
    try {
      setProcessing(true);
      setMessages(prev => [...prev, { role: "user", content: transcript }]);

      addAgentLog('ConversationalAgent', 'RECEIVED', `User said: "${transcript}"`);

      const chatResponse = await axios.post(`${API}/chat`, {
        message: transcript,
        conversation_id: conversationId
      });

      const aiResponse = chatResponse.data.message;
      const imageData = chatResponse.data.image_base64;
      const promptUsed = chatResponse.data.prompt_used;
      
      if (!conversationId) {
        setConversationId(chatResponse.data.conversation_id);
      }

      addAgentLog('ConversationalAgent', 'PROCESSING', 'Analyzing user intent...');
      
      if (chatResponse.data.ready_to_plan) {
        addAgentLog('ConversationalAgent', 'COMPLETE', 'Requirements gathered. Creating campaign...');
        addAgentLog('Orchestrator', 'ROUTING', 'Assigning to Planning Agent');
        addAgentLog('PlanningAgent', 'STARTED', 'Creating strategic plan...');
        
        setTimeout(() => {
          addAgentLog('PlanningAgent', 'COMPLETE', 'Plan created. Assigning tasks to specialist agents');
          addAgentLog('MarketResearchAgent', 'ASSIGNED', 'Task: Analyze target audience');
          addAgentLog('ContentAgent', 'ASSIGNED', 'Task: Generate campaign content');
          addAgentLog('SocialMediaAgent', 'ASSIGNED', 'Task: Create social media strategy');
        }, 1500);
      } else {
        addAgentLog('ConversationalAgent', 'RESPONSE', 'Asking clarifying questions');
      }

      // Add message with image data if available
      const assistantMessage = { 
        role: "assistant", 
        content: aiResponse,
        image: imageData,
        prompt: promptUsed
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Log image generation if it happened
      if (imageData) {
        addAgentLog('ImageGenerationAgent', 'COMPLETE', `Generated image using DALL-E`);
        toast.success('🎨 Image generated!');
      }
      
      speakText(aiResponse);

      if (chatResponse.data.ready_to_plan && chatResponse.data.campaign_id) {
        toast.success('Campaign created!');
        setTimeout(() => navigate(`/campaign/${chatResponse.data.campaign_id}`), 3000);
      }

    } catch (error) {
      toast.error('Failed to process your message.');
      addAgentLog('System', 'ERROR', 'Failed to process request');
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg bg-black/30 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/')}
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-semibold">Voice Assistant with Agent Visualization</span>
            </div>
          </div>
          
          <div className="flex items-center justify-center gap-2">
            <span className="text-sm text-slate-300">Language:</span>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-white/10 text-white border border-white/20 rounded-lg px-3 py-1.5 text-sm backdrop-blur-lg"
              style={{colorScheme: 'dark'}}
            >
              <option value="en-US" className="bg-slate-800 text-white">🇺🇸 English</option>
              <option value="te-IN" className="bg-slate-800 text-white">🇮🇳 Telugu</option>
              <option value="ta-IN" className="bg-slate-800 text-white">🇮🇳 Tamil</option>
              <option value="kn-IN" className="bg-slate-800 text-white">🇮🇳 Kannada</option>
              <option value="hi-IN" className="bg-slate-800 text-white">🇮🇳 Hindi</option>
              <option value="es-ES" className="bg-slate-800 text-white">🇪🇸 Spanish</option>
              <option value="fr-FR" className="bg-slate-800 text-white">🇫🇷 French</option>
              <option value="de-DE" className="bg-slate-800 text-white">🇩🇪 German</option>
            </select>
          </div>
        </div>
      </div>

      {/* Split Screen Layout */}
      <div className="pt-32 pb-40 px-6 h-screen">
        <div className="max-w-7xl mx-auto h-full grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* LEFT: User Conversation */}
          <Card className="backdrop-blur-lg bg-black/30 border-white/20 p-6 overflow-y-auto">
            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/20">
              <MessageSquare className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-semibold text-white">Your Conversation</h3>
            </div>
            
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div 
                  key={idx}
                  className={`p-4 rounded-xl ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 ml-8'
                      : 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 mr-8'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-300 mb-1">
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </p>
                  <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  
                  {/* Display image if available */}
                  {msg.image && (
                    <div className="mt-4">
                      <img 
                        src={`data:image/png;base64,${msg.image}`}
                        alt={msg.prompt || "Generated image"}
                        className="rounded-lg max-w-full h-auto border-2 border-white/20 shadow-lg"
                      />
                      {msg.prompt && (
                        <p className="text-xs text-slate-400 mt-2 italic">
                          Prompt: {msg.prompt}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </Card>

          {/* RIGHT: Agent Communication */}
          <Card className="backdrop-blur-lg bg-black/30 border-white/20 p-6 overflow-y-auto">
            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/20">
              <Users className="w-5 h-5 text-purple-400" />
              <h3 className="text-lg font-semibold text-white">Agent Communication</h3>
            </div>
            
            {agentLogs.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">Agents will communicate here when you start a conversation</p>
              </div>
            ) : (
              <div className="space-y-3">
                {agentLogs.map((log, idx) => (
                  <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10 animate-fade-in">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-purple-400">{log.agent}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        log.action === 'COMPLETE' ? 'bg-green-500/20 text-green-400' :
                        log.action === 'ERROR' ? 'bg-red-500/20 text-red-400' :
                        log.action === 'ASSIGNED' ? 'bg-blue-500/20 text-blue-400' :
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
          </Card>
        </div>
      </div>

      {/* Voice Control & Text Input */}
      <div className="fixed bottom-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-6 pb-8">
          <Card className="backdrop-blur-2xl bg-black/40 border-white/20 p-6 shadow-2xl">
            <div className="space-y-4">
              {/* Text Input Row */}
              <div className="flex gap-3 items-center">
                <Input
                  value={textMessage}
                  onChange={(e) => setTextMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendTextMessage()}
                  placeholder="Type your message here..."
                  className="flex-1 bg-white/10 text-white border-white/20 placeholder:text-slate-400"
                  disabled={processing}
                />
                <Button
                  onClick={handleSendTextMessage}
                  disabled={processing || !textMessage.trim()}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Voice Control Row */}
              <div className="flex items-center justify-between">
                <div className="text-left">
                  <p className="text-lg font-semibold text-white mb-1">
                    {isListening ? '🎤 Listening...' : isSpeaking ? '🔊 Speaking...' : processing ? '⚙️ Processing...' : '✅ Ready'}
                  </p>
                  <p className="text-sm text-slate-400">
                    {isListening ? 'Speak clearly' : isSpeaking ? 'Playing response' : processing ? 'Agents working...' : 'Type or click mic'}
                  </p>
                </div>

                <div className="flex gap-4">
                  <Button
                    size="lg"
                    disabled={processing || isSpeaking}
                    onClick={isListening ? stopListening : startListening}
                    className={`w-20 h-20 rounded-full ${
                      isListening
                        ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse'
                        : 'bg-gradient-to-br from-cyan-500 to-blue-500'
                    } shadow-2xl`}
                  >
                    {isListening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                  </Button>
                  
                  {isSpeaking && (
                    <Button
                      size="lg"
                      onClick={stopSpeaking}
                      className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-500 to-red-500"
                    >
                      ⏸️
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantWithAgents;
