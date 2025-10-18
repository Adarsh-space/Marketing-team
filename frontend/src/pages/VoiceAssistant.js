import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sparkles, Mic, MicOff, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VoiceAssistant = () => {
  const navigate = useNavigate();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [processing, setProcessing] = useState(false);
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  // Initialize Speech Recognition and Synthesis
  useEffect(() => {
    // Initialize Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Transcript:', transcript);
        
        // Stop listening
        setIsListening(false);
        
        // Process the transcript
        await processTranscript(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        
        if (event.error === 'no-speech') {
          toast.error('No speech detected. Please try again.');
        } else if (event.error === 'not-allowed') {
          toast.error('Microphone access denied. Please allow microphone access.');
        } else {
          toast.error('Speech recognition error. Please try again.');
        }
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    // Initialize Speech Synthesis
    synthRef.current = window.speechSynthesis;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Start listening
  const startListening = () => {
    if (!recognitionRef.current) {
      toast.error('Speech recognition not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    try {
      recognitionRef.current.start();
      setIsListening(true);
      toast.success('Listening... Speak now!');
    } catch (err) {
      console.error('Error starting recognition:', err);
      toast.error('Failed to start listening. Please try again.');
    }
  };

  // Stop listening
  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  // Process transcript
  const processTranscript = async (transcript) => {
    try {
      setProcessing(true);
      
      // Add user message
      setMessages(prev => [...prev, { role: "user", content: transcript }]);

      // Get AI response
      const chatResponse = await axios.post(`${API}/chat`, {
        message: transcript,
        conversation_id: conversationId
      });

      const aiResponse = chatResponse.data.message;
      
      if (!conversationId) {
        setConversationId(chatResponse.data.conversation_id);
      }

      // Add AI response
      setMessages(prev => [...prev, { role: "assistant", content: aiResponse }]);

      // Speak the response
      speakText(aiResponse);

      // Check if campaign created
      if (chatResponse.data.ready_to_plan && chatResponse.data.campaign_id) {
        toast.success('Campaign created! Redirecting...');
        setTimeout(() => {
          navigate(`/campaign/${chatResponse.data.campaign_id}`);
        }, 3000);
      }

    } catch (error) {
      console.error('Processing error:', error);
      toast.error('Failed to process your message. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  // Speak text using browser TTS
  const speakText = (text) => {
    if (!synthRef.current) return;

    // Cancel any ongoing speech
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    // Try to use a good quality voice
    const voices = synthRef.current.getVoices();
    const goodVoice = voices.find(v => 
      v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Microsoft'))
    );
    if (goodVoice) {
      utterance.voice = goodVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg bg-black/30 border-b border-white/10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
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
            <span className="text-white font-semibold">Voice Assistant</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-24 pb-40 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Messages */}
          <div className="space-y-6 mb-8">
            {messages.length === 0 && (
              <div className="text-center py-20">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mx-auto mb-6 animate-pulse">
                  <Mic className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-3">Start a Conversation</h2>
                <p className="text-lg text-slate-300 mb-2">Click the microphone to begin</p>
                <p className="text-sm text-slate-400">Powered by Browser Speech Recognition</p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <Card 
                key={idx}
                className={`p-6 ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-500/30 ml-12' 
                    : 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/30 mr-12'
                } backdrop-blur-lg border animate-fade-in`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-cyan-500 to-blue-500'
                      : 'bg-gradient-to-br from-purple-500 to-pink-500'
                  }`}>
                    {msg.role === 'user' ? (
                      <Mic className="w-5 h-5 text-white" />
                    ) : (
                      <Sparkles className="w-5 h-5 text-white" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-300 mb-1">
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </p>
                    <p className="text-white leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Voice Control */}
      <div className="fixed bottom-0 left-0 right-0 z-50">
        <div className="max-w-4xl mx-auto px-6 pb-8">
          <Card className="backdrop-blur-2xl bg-black/40 border-white/20 p-8 shadow-2xl">
            {/* Status */}
            <div className="text-center mb-6">
              <p className="text-2xl font-semibold text-white mb-2">
                {isListening ? '🎤 Listening...' : isSpeaking ? '🔊 Speaking...' : processing ? '⚙️ Processing...' : '✅ Ready'}
              </p>
              <p className="text-slate-400">
                {isListening ? 'Speak clearly into your microphone' : isSpeaking ? 'Playing AI response' : processing ? 'Getting AI response...' : 'Click the button to start'}
              </p>
            </div>

            {/* Control Button */}
            <div className="flex justify-center gap-4">
              <Button
                size="lg"
                disabled={processing || isSpeaking}
                onClick={isListening ? stopListening : startListening}
                className={`w-24 h-24 rounded-full ${
                  isListening
                    ? 'bg-gradient-to-br from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 animate-pulse'
                    : 'bg-gradient-to-br from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600'
                } shadow-2xl transition-all duration-300 hover:scale-110`}
                data-testid="voice-button"
              >
                {isListening ? (
                  <MicOff className="w-10 h-10 text-white" />
                ) : (
                  <Mic className="w-10 h-10 text-white" />
                )}
              </Button>
              
              {isSpeaking && (
                <Button
                  size="lg"
                  onClick={stopSpeaking}
                  className="w-24 h-24 rounded-full bg-gradient-to-br from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 shadow-2xl"
                >
                  ⏸️
                </Button>
              )}
            </div>

            {/* Helper Text */}
            <div className="mt-6 text-center text-sm text-slate-400">
              <p>Click to {isListening ? 'stop' : 'start'} • Free Browser Speech Recognition</p>
              <p className="text-xs mt-1">Works best in Chrome or Edge</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistant;
