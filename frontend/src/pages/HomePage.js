import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sparkles, Send, TrendingUp, Zap, Target, BarChart3, Mail, Share2, Search, DollarSign, ArrowRight, Check, Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { useVoice } from "@/hooks/useVoice";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HomePage = () => {
  const navigate = useNavigate();
  const [showChat, setShowChat] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hubspotConnected, setHubspotConnected] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [languages, setLanguages] = useState({});

  // Voice hook with automatic transcription
  const handleTranscript = (transcript) => {
    setMessage(transcript);
    // Auto-send after voice input
    setTimeout(() => {
      handleSendMessage(transcript);
    }, 500);
  };

  const { 
    isListening, 
    isSpeaking, 
    audioLevel,
    startListening, 
    stopListening, 
    speak, 
    stopSpeaking 
  } = useVoice(handleTranscript, selectedLanguage);

  useEffect(() => {
    // Check HubSpot connection status
    checkHubSpotStatus();
    
    // Load supported languages
    loadLanguages();
    
    // Check if redirected from HubSpot OAuth
    const params = new URLSearchParams(window.location.search);
    if (params.get('hubspot_connected') === 'true') {
      toast.success('HubSpot connected successfully!');
      setHubspotConnected(true);
      // Clean URL
      window.history.replaceState({}, '', '/');
    }
  }, []);

  // Start/stop continuous listening when voice is enabled
  useEffect(() => {
    if (voiceEnabled && showChat && !isListening && !loading) {
      startListening();
    } else if (!voiceEnabled && isListening) {
      stopListening();
    }
  }, [voiceEnabled, showChat, isListening, loading, startListening, stopListening]);

  const loadLanguages = async () => {
    try {
      const response = await axios.get(`${API}/voice/languages`);
      setLanguages(response.data.languages);
    } catch (error) {
      console.error('Error loading languages:', error);
    }
  };

  const checkHubSpotStatus = async () => {
    try {
      const response = await axios.get(`${API}/hubspot/status`);
      setHubspotConnected(response.data.connected);
    } catch (error) {
      console.error('Error checking HubSpot status:', error);
    }
  };

  const handleConnectHubSpot = async () => {
    try {
      const response = await axios.get(`${API}/oauth/hubspot/authorize`);
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error('Failed to connect HubSpot');
    }
  };

  const handleSendMessage = async (textOverride = null) => {
    const textToSend = textOverride || message;
    if (!textToSend.trim()) return;

    setLoading(true);
    setMessage("");

    // Add user message to UI
    const newUserMessage = { role: "user", content: textToSend };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: textToSend,
        conversation_id: conversationId
      });

      const data = response.data;
      
      // Set conversation ID
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      // Add assistant response
      const assistantMessage = { role: "assistant", content: data.message };
      setMessages(prev => [...prev, assistantMessage]);

      // Speak the response if auto-speak is enabled
      if (autoSpeak && !isSpeaking) {
        await speak(data.message);
      }

      // Check if campaign was created
      if (data.ready_to_plan && data.campaign_id) {
        toast.success('Campaign created! Executing plan...');
        
        // Navigate to campaign page after a short delay
        setTimeout(() => {
          navigate(`/campaign/${data.campaign_id}`);
        }, 1500);
      }

      // Restart listening if voice is enabled
      if (voiceEnabled && !isListening) {
        setTimeout(() => startListening(), 1000);
      }

    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to send message');
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Target className="w-8 h-8" />,
      title: "Strategic Planning",
      description: "AI-powered campaign strategies tailored to your goals"
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: "Market Research",
      description: "Deep insights into your target audience and competitors"
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: "Content Creation",
      description: "Generate compelling marketing content automatically"
    },
    {
      icon: <Mail className="w-8 h-8" />,
      title: "Email Marketing",
      description: "Personalized email campaigns that convert"
    },
    {
      icon: <Share2 className="w-8 h-8" />,
      title: "Social Media",
      description: "Multi-platform social media management"
    },
    {
      icon: <Search className="w-8 h-8" />,
      title: "SEO Optimization",
      description: "Improve your search rankings organically"
    },
    {
      icon: <DollarSign className="w-8 h-8" />,
      title: "PPC Advertising",
      description: "Maximize ROI with optimized paid campaigns"
    },
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: "Analytics & Reporting",
      description: "Real-time insights and performance tracking"
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass fixed top-0 left-0 right-0 z-50 border-b border-white/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              MarketAI
            </h1>
          </div>
          <div className="flex items-center gap-4">
            {hubspotConnected ? (
              <Badge className="bg-green-100 text-green-700 border-green-200" data-testid="hubspot-status-badge">
                <Check className="w-3 h-3 mr-1" />
                HubSpot Connected
              </Badge>
            ) : (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleConnectHubSpot}
                className="border-cyan-200 hover:bg-cyan-50"
                data-testid="connect-hubspot-btn"
              >
                Connect HubSpot
              </Button>
            )}
            <Button 
              variant="outline" 
              onClick={() => navigate('/dashboard')}
              className="border-cyan-200 hover:bg-cyan-50"
              data-testid="dashboard-nav-btn"
            >
              Dashboard
            </Button>
            <Button 
              onClick={() => setShowChat(true)}
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white shadow-lg shadow-cyan-500/30"
              data-testid="start-campaign-btn"
            >
              <Zap className="w-4 h-4 mr-2" />
              Start Campaign
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-cyan-100 text-cyan-700 border-cyan-200 px-4 py-1.5 text-sm font-medium" data-testid="hero-badge">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            AI-Powered Marketing Automation
          </Badge>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent leading-tight" data-testid="hero-title">
            Transform Your Marketing
            <br />with AI Agents
          </h1>
          
          <p className="text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed" data-testid="hero-description">
            Tell us your goals. Our multi-agent AI system creates, executes, and optimizes
            complete marketing campaigns across all channels—automatically.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              size="lg" 
              onClick={() => setShowChat(true)}
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-8 py-6 text-lg shadow-xl shadow-cyan-500/30 rounded-xl"
              data-testid="get-started-hero-btn"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              onClick={() => navigate('/dashboard')}
              className="px-8 py-6 text-lg border-2 border-cyan-200 hover:bg-cyan-50 rounded-xl"
              data-testid="view-examples-btn"
            >
              View Dashboard
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 bg-white/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4 text-slate-800" data-testid="features-title">Complete Marketing Automation</h2>
            <p className="text-lg text-slate-600" data-testid="features-subtitle">Powered by specialized AI agents working together</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                className="p-6 glass border-white/30 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
                data-testid={`feature-card-${index}`}
              >
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mb-4 text-white shadow-lg shadow-cyan-500/30">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2 text-slate-800">{feature.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Chat Modal */}
      {showChat && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" data-testid="chat-modal">
          <Card className="w-full max-w-2xl h-[600px] flex flex-col glass border-white/30 shadow-2xl">
            {/* Chat Header */}
            <div className="p-6 border-b border-white/20">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-800" data-testid="chat-title">AI Marketing Assistant</h3>
                    <p className="text-sm text-slate-500">Tell me about your marketing goals</p>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    setShowChat(false);
                    if (voiceEnabled) {
                      setVoiceEnabled(false);
                      stopListening();
                    }
                  }}
                  data-testid="close-chat-btn"
                >
                  ✕
                </Button>
              </div>

              {/* Voice Controls */}
              <div className="flex flex-wrap gap-3 items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant={voiceEnabled ? "default" : "outline"}
                    onClick={() => {
                      setVoiceEnabled(!voiceEnabled);
                      if (!voiceEnabled) {
                        toast.success('Voice mode enabled - speak anytime!');
                      } else {
                        stopListening();
                        toast.info('Voice mode disabled');
                      }
                    }}
                    className={voiceEnabled ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white" : "border-slate-200"}
                    data-testid="toggle-voice-btn"
                  >
                    {voiceEnabled ? <Mic className="w-4 h-4 mr-2" /> : <MicOff className="w-4 h-4 mr-2" />}
                    {voiceEnabled ? 'Voice On' : 'Voice Off'}
                  </Button>

                  <Button
                    size="sm"
                    variant={autoSpeak ? "default" : "outline"}
                    onClick={() => {
                      setAutoSpeak(!autoSpeak);
                      if (!autoSpeak) {
                        toast.success('Auto-speak enabled');
                      } else {
                        stopSpeaking();
                        toast.info('Auto-speak disabled');
                      }
                    }}
                    className={autoSpeak ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white" : "border-slate-200"}
                    data-testid="toggle-speak-btn"
                  >
                    {autoSpeak ? <Volume2 className="w-4 h-4 mr-2" /> : <VolumeX className="w-4 h-4 mr-2" />}
                    {autoSpeak ? 'Speaker On' : 'Speaker Off'}
                  </Button>
                </div>

                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger className="w-36 h-9 border-slate-200" data-testid="language-select">
                    <SelectValue placeholder="Language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">🇬🇧 English</SelectItem>
                    <SelectItem value="es">🇪🇸 Spanish</SelectItem>
                    <SelectItem value="fr">🇫🇷 French</SelectItem>
                    <SelectItem value="de">🇩🇪 German</SelectItem>
                    <SelectItem value="it">🇮🇹 Italian</SelectItem>
                    <SelectItem value="pt">🇵🇹 Portuguese</SelectItem>
                    <SelectItem value="zh">🇨🇳 Chinese</SelectItem>
                    <SelectItem value="ja">🇯🇵 Japanese</SelectItem>
                    <SelectItem value="ar">🇸🇦 Arabic</SelectItem>
                    <SelectItem value="hi">🇮🇳 Hindi</SelectItem>
                    <SelectItem value="ru">🇷🇺 Russian</SelectItem>
                    <SelectItem value="ko">🇰🇷 Korean</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Voice Status Indicator */}
              {voiceEnabled && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${isListening ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                    <span className="text-sm font-medium text-green-700">
                      {isListening ? 'Listening...' : 'Ready to listen'}
                    </span>
                  </div>
                  {isListening && (
                    <div className="flex gap-1 items-end h-8">
                      {[...Array(20)].map((_, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-green-500 rounded-t transition-all duration-75"
                          style={{
                            height: `${Math.max(10, (audioLevel / 255) * 100 * (0.5 + Math.random() * 0.5))}%`,
                            opacity: 0.7
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="chat-messages">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-cyan-500/30">
                    <Sparkles className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="text-lg font-semibold mb-2 text-slate-800">Start Your Campaign</h4>
                  <p className="text-sm text-slate-600">Describe your product and marketing goals to begin</p>
                </div>
              )}
              
              {messages.map((msg, index) => (
                <div 
                  key={index} 
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-in`}
                  data-testid={`message-${index}`}
                >
                  <div 
                    className={`max-w-[80%] p-4 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30'
                        : 'bg-white text-slate-800 shadow-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start animate-fade-in">
                  <div className="bg-white p-4 rounded-2xl shadow-md">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-6 border-t border-white/20">
              <div className="flex gap-3">
                <Input 
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                  placeholder="Describe your product and marketing goals..."
                  className="flex-1 bg-white border-slate-200 focus:border-cyan-400 rounded-xl"
                  disabled={loading}
                  data-testid="chat-input"
                />
                <Button 
                  onClick={handleSendMessage}
                  disabled={loading || !message.trim()}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-6 rounded-xl shadow-lg shadow-cyan-500/30"
                  data-testid="send-message-btn"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default HomePage;
